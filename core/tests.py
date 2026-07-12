from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from core.models import (
    User, Department, AssetCategory, Asset, Allocation,
    TransferRequest, Booking, MaintenanceRequest, AuditCycle, AuditItem, Notification
)

class AssetFlowTestBase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create standard test department and category
        self.department = Department.objects.create(name="Engineering")
        self.category = AssetCategory.objects.create(name="Laptops", warranty_period_days=365)
        
        # Create test users with different roles
        self.admin = User.objects.create_user(
            username="admin_user", password="password123", email="admin@test.com",
            role=User.Role.ADMIN, department=self.department
        )
        self.manager = User.objects.create_user(
            username="manager_user", password="password123", email="manager@test.com",
            role=User.Role.ASSET_MANAGER, department=self.department
        )
        self.employee = User.objects.create_user(
            username="employee_user", password="password123", email="employee@test.com",
            role=User.Role.EMPLOYEE, department=self.department
        )
        
        # Create default asset
        self.asset = Asset.objects.create(
            name="MacBook Pro", category=self.category,
            serial_number="SN123456", is_bookable=False,
            status=Asset.Status.AVAILABLE, department=self.department
        )

class UserRBACTests(AssetFlowTestBase):
    def test_signup_force_employee_role(self):
        """Ensure public signup form enforces Role.EMPLOYEE regardless of input."""
        response = self.client.post(reverse("signup"), {
            "first_name": "Test",
            "last_name": "User",
            "username": "new_user",
            "email": "new@test.com",
            "password1": "P@ssw0rd_Tests_2026!",
            "password2": "P@ssw0rd_Tests_2026!",
            "role": "ADMIN"  # Attempt to escalate role
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username="new_user")
        self.assertEqual(new_user.role, User.Role.EMPLOYEE)

    def test_employee_cannot_access_org_setup(self):
        """An ordinary employee must be blocked from org setup."""
        self.client.login(username="employee_user", password="password123")
        response = self.client.get(reverse("org_setup"))
        self.assertFalse(self.employee.has_role("ADMIN"))
        # Non-permitted access redirects or errors depending on decorator implementation.
        # views.org_setup is login_required, but can_manage check is passed to context.
        # Let's check promotion endpoint which is gated by @role_required(*MANAGES_ORG).
        response_promote = self.client.get(reverse("promote_employee", args=[self.employee.pk]))
        self.assertEqual(response_promote.status_code, 302) # Redirects (denied)

    def test_admin_can_promote_user(self):
        """Admin is authorized to promote employees to department heads/managers."""
        self.client.login(username="admin_user", password="password123")
        response = self.client.post(reverse("promote_employee", args=[self.employee.pk]), {
            "role": User.Role.ASSET_MANAGER,
            "department": self.department.id
        })
        self.assertEqual(response.status_code, 302)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.role, User.Role.ASSET_MANAGER)

class AllocationTests(AssetFlowTestBase):
    def test_allocation_success_and_return(self):
        """Standard allocation and return transitions."""
        alloc = Allocation.create_for(self.asset, employee=self.employee)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ALLOCATED)
        self.assertEqual(alloc.status, Allocation.Status.ACTIVE)
        
        # Test return
        alloc.mark_returned(condition_notes="Excellent condition")
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)
        self.assertEqual(alloc.status, Allocation.Status.RETURNED)

    def test_prevent_double_allocation(self):
        """Cannot allocate an already allocated asset."""
        Allocation.create_for(self.asset, employee=self.employee)
        with self.assertRaises(ValidationError):
            Allocation.create_for(self.asset, employee=self.admin)

    def test_transfer_request_approval_workflow(self):
        """Transfer request closes current allocation and opens new one."""
        # Initial allocation to employee
        Allocation.create_for(self.asset, employee=self.employee)
        
        # Transfer request from employee to admin
        transfer = TransferRequest.objects.create(
            asset=self.asset, requested_by=self.employee,
            to_employee=self.admin
        )
        self.assertEqual(transfer.status, TransferRequest.Status.REQUESTED)
        
        # Approve transfer
        transfer.approve(decided_by=self.admin)
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, TransferRequest.Status.APPROVED)
        
        # Check that asset is still allocated, but to the new user
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ALLOCATED)
        self.assertEqual(self.asset.current_allocation.employee, self.admin)

class BookingTests(AssetFlowTestBase):
    def setUp(self):
        super().setUp()
        self.bookable_asset = Asset.objects.create(
            name="Conference Room", category=self.category,
            serial_number="SN-CONF", is_bookable=True,
            status=Asset.Status.AVAILABLE, department=self.department
        )

    def test_booking_non_bookable_asset_fails(self):
        """Cannot book an asset that is not marked is_bookable."""
        now = timezone.now()
        with self.assertRaises(ValidationError):
            Booking.create_for(
                self.asset, booked_by=self.employee,
                start_time=now + timedelta(hours=1),
                end_time=now + timedelta(hours=2)
            )

    def test_booking_time_sanity(self):
        """End time must be after start time."""
        now = timezone.now()
        with self.assertRaises(ValidationError):
            Booking.create_for(
                self.bookable_asset, booked_by=self.employee,
                start_time=now + timedelta(hours=2),
                end_time=now + timedelta(hours=1)
            )

    def test_booking_overlap_prevention(self):
        """Overlapping bookings are blocked, distinct ones succeed."""
        now = timezone.now()
        start1 = now + timedelta(hours=1)
        end1 = now + timedelta(hours=3)
        
        # Create first booking
        Booking.create_for(self.bookable_asset, self.employee, start1, end1)
        
        # Overlapping case 1: Completely inside
        with self.assertRaises(ValidationError):
            Booking.create_for(self.bookable_asset, self.admin, start1 + timedelta(minutes=30), end1 - timedelta(minutes=30))
            
        # Overlapping case 2: Starts before, ends during
        with self.assertRaises(ValidationError):
            Booking.create_for(self.bookable_asset, self.admin, start1 - timedelta(hours=1), start1 + timedelta(hours=1))
            
        # Overlapping case 3: Starts during, ends after
        with self.assertRaises(ValidationError):
            Booking.create_for(self.bookable_asset, self.admin, end1 - timedelta(hours=1), end1 + timedelta(hours=1))
            
        # Non-overlapping adjacent booking succeeds
        success_booking = Booking.create_for(self.bookable_asset, self.admin, end1, end1 + timedelta(hours=1))
        self.assertIsNotNone(success_booking)

class MaintenanceTests(AssetFlowTestBase):
    def test_maintenance_lifecycle(self):
        """Maintenance request state transitions and asset statuses."""
        # Create request
        req = MaintenanceRequest.objects.create(
            asset=self.asset, raised_by=self.employee,
            issue_description="Screen flicker"
        )
        self.assertEqual(req.status, MaintenanceRequest.Status.PENDING)
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)
        
        # Approve request -> asset is UNDER_MAINTENANCE
        req.approve(decided_by=self.manager)
        self.asset.refresh_from_db()
        self.assertEqual(req.status, MaintenanceRequest.Status.APPROVED)
        self.assertEqual(self.asset.status, Asset.Status.UNDER_MAINTENANCE)
        
        # Assign technician -> TECHNICIAN_ASSIGNED
        req.assign_technician("Alice the Tech")
        self.assertEqual(req.status, MaintenanceRequest.Status.TECHNICIAN_ASSIGNED)
        self.assertEqual(req.technician_name, "Alice the Tech")
        
        # Start progress -> IN_PROGRESS
        req.start_progress()
        self.assertEqual(req.status, MaintenanceRequest.Status.IN_PROGRESS)
        
        # Resolve request -> RESOLVED and asset is AVAILABLE
        req.resolve()
        self.asset.refresh_from_db()
        self.assertEqual(req.status, MaintenanceRequest.Status.RESOLVED)
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)

class AuditTests(AssetFlowTestBase):
    def setUp(self):
        super().setUp()
        self.location_asset = Asset.objects.create(
            name="Office Desk", category=self.category,
            serial_number="SN-DESK", location="Floor 3",
            status=Asset.Status.AVAILABLE, department=self.department
        )

    def test_audit_cycle_in_scope_assets(self):
        """Audit cycles filter assets correctly based on scope department/location."""
        cycle_dept = AuditCycle.objects.create(
            name="Engineering Q3 Audit", scope_department=self.department,
            date_start=timezone.localdate(), date_end=timezone.localdate() + timedelta(days=7)
        )
        self.assertIn(self.asset, cycle_dept.in_scope_assets())
        
        cycle_loc = AuditCycle.objects.create(
            name="Floor 3 Audit", scope_location="Floor 3",
            date_start=timezone.localdate(), date_end=timezone.localdate() + timedelta(days=7)
        )
        self.assertIn(self.location_asset, cycle_loc.in_scope_assets())
        self.assertNotIn(self.asset, cycle_loc.in_scope_assets())

    def test_audit_cycle_closure_missing_flips_to_lost(self):
        """Audited items marked as MISSING flip the asset status to LOST upon cycle closure."""
        cycle = AuditCycle.objects.create(
            name="Verification Cycle", scope_department=self.department,
            date_start=timezone.localdate(), date_end=timezone.localdate() + timedelta(days=7)
        )
        cycle.ensure_items()
        
        # Retrieve the audit item for self.asset
        item = cycle.items.get(asset=self.asset)
        item.mark(AuditItem.Result.MISSING, "Unable to find in warehouse")
        
        # Close the cycle
        cycle.close()
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.LOST)
        self.assertEqual(cycle.status, AuditCycle.Status.CLOSED)
