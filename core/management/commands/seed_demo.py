from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import (Allocation, Asset, AssetCategory, AuditCycle, Booking,
                          Department, MaintenanceRequest)

User = get_user_model()


class Command(BaseCommand):
    help = ("Seed demo users, departments, categories, and sample assets for "
            "AssetFlow. Development only — creates well-known demo credentials "
            "(admin/admin1234, etc.), so it refuses to run when DEBUG is False.")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "seed_demo creates well-known demo credentials (admin/admin1234, "
                "pass1234, ...) and must not be run against a production "
                "(DEBUG=False) deployment."
            )
        self.stdout.write("Seeding AssetFlow demo data...")

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin1234", role=User.Role.ADMIN)
            self.stdout.write("  created superuser 'admin' / admin1234")

        it, _ = Department.objects.get_or_create(name="IT")
        ops, _ = Department.objects.get_or_create(name="Operations")

        def make_user(username, first, last, role, dept):
            user, created = User.objects.get_or_create(
                username=username,
                defaults=dict(first_name=first, last_name=last, role=role, department=dept,
                              email=f"{username}@example.com"),
            )
            if created:
                user.set_password("pass1234")
                user.save()
                self.stdout.write(f"  created user '{username}' / pass1234 ({role})")
            return user

        dept_head = make_user("dept_head1", "Deepa", "Head", User.Role.DEPARTMENT_HEAD, it)
        asset_mgr = make_user("asset_mgr1", "Aman", "Manager", User.Role.ASSET_MANAGER, ops)
        priya = make_user("priya", "Priya", "Shah", User.Role.EMPLOYEE, it)
        raj = make_user("raj", "Raj", "Verma", User.Role.EMPLOYEE, it)

        it.head = dept_head
        it.save(update_fields=["head"])

        electronics, _ = AssetCategory.objects.get_or_create(
            name="Electronics", defaults=dict(warranty_period_days=365))
        furniture, _ = AssetCategory.objects.get_or_create(name="Furniture")
        rooms, _ = AssetCategory.objects.get_or_create(name="Meeting rooms")

        laptop, _ = Asset.objects.get_or_create(
            serial_number="SN-LAPTOP-114",
            defaults=dict(name="Laptop", category=electronics, acquisition_date=date.today() - timedelta(days=200),
                          acquisition_cost=1200, condition="Good", location="IT floor", department=it),
        )
        Asset.objects.get_or_create(
            serial_number="SN-LAPTOP-115",
            defaults=dict(name="Laptop", category=electronics, acquisition_date=date.today() - timedelta(days=90),
                          acquisition_cost=1250, condition="Good", location="IT floor", department=it),
        )
        projector, _ = Asset.objects.get_or_create(
            serial_number="SN-PROJ-062",
            defaults=dict(name="Projector", category=electronics, acquisition_date=date.today() - timedelta(days=400),
                          acquisition_cost=600, condition="Fair", location="Storage", department=ops),
        )
        room_b2, _ = Asset.objects.get_or_create(
            serial_number="SN-ROOM-B2",
            defaults=dict(name="Room B2", category=rooms, acquisition_date=date.today() - timedelta(days=1000),
                          acquisition_cost=0, condition="Good", location="2nd floor", is_bookable=True, department=ops),
        )
        Asset.objects.get_or_create(
            serial_number="SN-CHAIR-01",
            defaults=dict(name="Ergonomic chair", category=furniture, acquisition_date=date.today() - timedelta(days=500),
                          acquisition_cost=300, condition="Good", location="Storage"),
        )

        # Priya holds the laptop, matching the brief's own worked example
        if laptop.status == Asset.Status.AVAILABLE:
            Allocation.create_for(laptop, employee=priya, expected_return_date=date.today() + timedelta(days=180))
            self.stdout.write("  allocated laptop AF-0001-ish to Priya (matches the brief's example)")

        # An overdue allocation, to populate the dashboard's overdue panel
        overdue_asset, created = Asset.objects.get_or_create(
            serial_number="SN-TABLET-01",
            defaults=dict(name="Tablet", category=electronics, acquisition_date=date.today() - timedelta(days=300),
                          acquisition_cost=400, condition="Good", location="IT floor"),
        )
        if created:
            alloc = Allocation.objects.create(asset=overdue_asset, employee=raj,
                                               expected_return_date=date.today() - timedelta(days=5))
            overdue_asset.status = Asset.Status.ALLOCATED
            overdue_asset.save(update_fields=["status"])

        # One resolved maintenance request (Projector, per the brief's example) + one pending
        MaintenanceRequest.objects.get_or_create(
            asset=projector, raised_by=raj,
            defaults=dict(issue_description="Bulb flickering, needs replacement", priority="MEDIUM"),
        )

        # A confirmed booking on Room B2, matching the brief's overlap example (9:00-10:00)
        today = timezone.localdate()
        start = timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()) + timedelta(hours=9))
        end = start + timedelta(hours=1)
        if not Booking.objects.filter(asset=room_b2, start_time=start).exists():
            Booking.objects.create(asset=room_b2, booked_by=dept_head, start_time=start, end_time=end)

        # An open audit cycle scoped to IT
        cycle, created = AuditCycle.objects.get_or_create(
            name="Q3 IT spot check",
            defaults=dict(scope_department=it, date_start=today, date_end=today + timedelta(days=14)),
        )
        if created:
            cycle.auditors.add(asset_mgr)
            cycle.ensure_items()

        self.stdout.write(self.style.SUCCESS(
            "Done. Logins: dept_head1 / asset_mgr1 / priya / raj, all pass1234. Admin: admin / admin1234."
        ))
