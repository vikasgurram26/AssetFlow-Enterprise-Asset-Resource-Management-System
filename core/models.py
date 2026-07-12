from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class User(AbstractUser):
    """Auth + RBAC.

    IMPORTANT — this is the spec's headline auth rule: signup must NEVER
    let someone pick their own role. Every account created through the
    public signup form (see views.signup) is forced to Role.EMPLOYEE
    server-side, no matter what the form receives. The only way a User's
    role changes after that is through promote_role(), which is only
    reachable from the Employee Directory screen and is itself gated to
    is_staff (Admin) users — see decorators.role_required("ADMIN") on
    views.promote_employee.
    """

    class Role(models.TextChoices):
        EMPLOYEE = "EMPLOYEE", "Employee"
        DEPARTMENT_HEAD = "DEPARTMENT_HEAD", "Department Head"
        ASSET_MANAGER = "ASSET_MANAGER", "Asset Manager"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    department = models.ForeignKey("Department", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="members")
    status = models.CharField(max_length=10, choices=[("ACTIVE", "Active"), ("INACTIVE", "Inactive")],
                               default="ACTIVE")

    def has_role(self, *roles):
        return self.role in roles or self.is_superuser

    def is_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    def __str__(self):
        return self.get_full_name() or self.username


class Department(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(max_length=100, unique=True)
    head = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="departments_headed",
                              limit_choices_to={"role__in": ["DEPARTMENT_HEAD", "ADMIN"]})
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AssetCategory(models.Model):
    """Optional category-specific fields are kept generic (one nullable
    warranty_period_days field) rather than a full dynamic-schema system —
    that's a real "phase 2" feature, not an 8-hour one. Add more optional
    fields here the same way if your team needs them."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    warranty_period_days = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Asset categories"

    def __str__(self):
        return self.name


class Asset(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        ALLOCATED = "ALLOCATED", "Allocated"
        RESERVED = "RESERVED", "Reserved"
        UNDER_MAINTENANCE = "UNDER_MAINTENANCE", "Under Maintenance"
        LOST = "LOST", "Lost"
        RETIRED = "RETIRED", "Retired"
        DISPOSED = "DISPOSED", "Disposed"

    asset_tag = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=150)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name="assets")
    serial_number = models.CharField(max_length=100, unique=True)
    acquisition_date = models.DateField(default=timezone.localdate)
    acquisition_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    condition = models.CharField(max_length=20, default="Good")
    location = models.CharField(max_length=150, blank=True)
    is_bookable = models.BooleanField(default=False, help_text="Shared resource — bookable by time slot (Screen 6)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="assets")

    class Meta:
        ordering = ["asset_tag"]

    def save(self, *args, **kwargs):
        if not self.asset_tag:
            self.asset_tag = self._generate_asset_tag()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_asset_tag():
        """AF-0001, AF-0002, ... — simple max+1, fine at hackathon scale.
        A real production system would use a DB sequence to avoid a race
        between two simultaneous registrations; noted here rather than
        silently hidden."""
        last = Asset.objects.exclude(asset_tag="").order_by("-id").first()
        n = 1
        if last and last.asset_tag.startswith("AF-"):
            try:
                n = int(last.asset_tag.split("-")[1]) + 1
            except (IndexError, ValueError):
                n = Asset.objects.count() + 1
        return f"AF-{n:04d}"

    def __str__(self):
        return f"{self.asset_tag} — {self.name}"

    @property
    def current_allocation(self):
        return self.allocations.filter(status=Allocation.Status.ACTIVE).first()

    @property
    def is_overdue(self):
        alloc = self.current_allocation
        return bool(alloc and alloc.expected_return_date and alloc.expected_return_date < timezone.localdate())


class Allocation(models.Model):
    """Who currently holds an asset. One asset can have at most one ACTIVE
    allocation at a time — that constraint IS the "prevent double
    allocation" rule, enforced in Allocation.create_for() below rather
    than at the DB level, so we can raise a friendly error with the
    current holder's name (per the brief's exact UX: 'currently held by
    Priya, offers a Transfer Request button instead')."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RETURNED = "RETURNED", "Returned"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="allocations")
    employee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="allocations")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="allocations")
    allocated_date = models.DateTimeField(auto_now_add=True)
    expected_return_date = models.DateField(null=True, blank=True)
    returned_date = models.DateTimeField(null=True, blank=True)
    condition_notes = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-allocated_date"]

    def __str__(self):
        holder = self.employee or self.department or "—"
        return f"{self.asset.asset_tag} -> {holder}"

    @classmethod
    def create_for(cls, asset, employee=None, department=None, expected_return_date=None):
        """The single entry point for allocating an asset. Raises
        ValidationError with the current holder's name if the asset is
        already allocated — callers (the view) catch this and show the
        Transfer Request option instead, per the brief's example."""
        if asset.status == Asset.Status.ALLOCATED:
            current = asset.current_allocation
            holder = current.employee or current.department if current else "someone"
            raise ValidationError(f"{asset} is currently held by {holder}. Use Transfer Request instead.")
        if asset.status not in (Asset.Status.AVAILABLE,):
            raise ValidationError(f"{asset} is {asset.get_status_display()} and can't be allocated right now.")

        with transaction.atomic():
            allocation = cls.objects.create(
                asset=asset, employee=employee, department=department,
                expected_return_date=expected_return_date,
            )
            asset.status = Asset.Status.ALLOCATED
            asset.save(update_fields=["status"])
            notify(employee, f"{asset} has been allocated to you.")
        return allocation

    def mark_returned(self, condition_notes=""):
        if self.status != self.Status.ACTIVE:
            raise ValidationError("This allocation is already closed.")
        with transaction.atomic():
            self.status = self.Status.RETURNED
            self.returned_date = timezone.now()
            self.condition_notes = condition_notes
            self.save(update_fields=["status", "returned_date", "condition_notes"])
            self.asset.status = Asset.Status.AVAILABLE
            self.asset.save(update_fields=["status"])


class TransferRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="transfer_requests")
    to_employee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="incoming_transfers")
    to_department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name="incoming_transfers")
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transfer_requests_made")
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)
    decided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="transfer_requests_decided")
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Transfer {self.asset.asset_tag} -> {self.to_employee or self.to_department} ({self.status})"

    def approve(self, decided_by):
        """Requested -> Approved. Closes the current holder's allocation
        (if any) and opens a fresh one for the new holder — that's the
        "history updated automatically" requirement."""
        if self.status != self.Status.REQUESTED:
            raise ValidationError("Only a Requested transfer can be approved.")
        with transaction.atomic():
            current = self.asset.current_allocation
            if current:
                current.mark_returned(condition_notes="Returned via transfer")
            Allocation.create_for(self.asset, employee=self.to_employee, department=self.to_department)
            self.status = self.Status.APPROVED
            self.decided_by = decided_by
            self.decided_at = timezone.now()
            self.save(update_fields=["status", "decided_by", "decided_at"])
            notify(self.to_employee, f"Transfer of {self.asset} to you has been approved.")

    def reject(self, decided_by):
        if self.status != self.Status.REQUESTED:
            raise ValidationError("Only a Requested transfer can be rejected.")
        self.status = self.Status.REJECTED
        self.decided_by = decided_by
        self.decided_at = timezone.now()
        self.save(update_fields=["status", "decided_by", "decided_at"])
        notify(self.requested_by, f"Transfer request for {self.asset} was rejected.")


class Booking(models.Model):
    """Time-slot booking of a shared/bookable asset. Overlap validation
    lives in create_for() — two bookings for the same asset conflict if
    (existing.start < new.end) AND (existing.end > new.start), the
    standard interval-overlap test. Status is a computed property, not a
    stored field that needs a cron job to keep current — "Upcoming /
    Ongoing / Completed" fall straight out of comparing start/end to
    now()."""

    class Status(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        ONGOING = "ONGOING", "Ongoing"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="bookings")
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.asset.asset_tag} {self.start_time:%b %d %H:%M}–{self.end_time:%H:%M}"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

    @property
    def status(self):
        if self.is_cancelled:
            return self.Status.CANCELLED
        now = timezone.now()
        if now < self.start_time:
            return self.Status.UPCOMING
        if now > self.end_time:
            return self.Status.COMPLETED
        return self.Status.ONGOING

    def get_status_display(self):
        return self.Status(self.status).label

    @classmethod
    def create_for(cls, asset, booked_by, start_time, end_time):
        if start_time >= end_time:
            raise ValidationError("End time must be after start time.")
        if not asset.is_bookable:
            raise ValidationError(f"{asset} is not marked as a bookable resource.")
        overlapping = cls.objects.filter(
            asset=asset, is_cancelled=False,
            start_time__lt=end_time, end_time__gt=start_time,
        )
        if overlapping.exists():
            clash = overlapping.first()
            raise ValidationError(
                f"{asset} is already booked {clash.start_time:%b %d %H:%M}–{clash.end_time:%H:%M}, "
                f"which overlaps your request."
            )
        booking = cls.objects.create(asset=asset, booked_by=booked_by, start_time=start_time, end_time=end_time)
        notify(booked_by, f"Booking confirmed: {asset} on {start_time:%b %d} {start_time:%H:%M}-{end_time:%H:%M}.")
        return booking

    def cancel(self):
        self.is_cancelled = True
        self.save(update_fields=["is_cancelled"])
        notify(self.booked_by, f"Booking for {self.asset} on {self.start_time:%b %d} was cancelled.")


class MaintenanceRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        TECHNICIAN_ASSIGNED = "TECHNICIAN_ASSIGNED", "Technician Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="maintenance_requests")
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="maintenance_requests_raised")
    issue_description = models.TextField()
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.PENDING)
    technician_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="maintenance_requests_decided")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.asset.asset_tag} — {self.issue_description[:40]}"

    def approve(self, decided_by):
        """Pending -> Approved. Asset flips to Under Maintenance
        automatically — per the brief, this is the moment the flip
        happens, not when the request is first raised."""
        if self.status != self.Status.PENDING:
            raise ValidationError("Only a Pending request can be approved.")
        with transaction.atomic():
            self.status = self.Status.APPROVED
            self.decided_by = decided_by
            self.save(update_fields=["status", "decided_by"])
            self.asset.status = Asset.Status.UNDER_MAINTENANCE
            self.asset.save(update_fields=["status"])
            notify(self.raised_by, f"Maintenance request for {self.asset} was approved.")

    def reject(self, decided_by):
        if self.status != self.Status.PENDING:
            raise ValidationError("Only a Pending request can be rejected.")
        self.status = self.Status.REJECTED
        self.decided_by = decided_by
        self.save(update_fields=["status", "decided_by"])
        notify(self.raised_by, f"Maintenance request for {self.asset} was rejected.")

    def assign_technician(self, technician_name):
        if self.status != self.Status.APPROVED:
            raise ValidationError("Assign a technician only after approval.")
        self.technician_name = technician_name
        self.status = self.Status.TECHNICIAN_ASSIGNED
        self.save(update_fields=["technician_name", "status"])

    def start_progress(self):
        if self.status != self.Status.TECHNICIAN_ASSIGNED:
            raise ValidationError("Assign a technician before starting work.")
        self.status = self.Status.IN_PROGRESS
        self.save(update_fields=["status"])

    def resolve(self):
        """-> Resolved. Asset returns to Available."""
        if self.status not in (self.Status.IN_PROGRESS, self.Status.APPROVED, self.Status.TECHNICIAN_ASSIGNED):
            raise ValidationError("This request isn't in a state that can be resolved.")
        with transaction.atomic():
            self.status = self.Status.RESOLVED
            self.resolved_at = timezone.now()
            self.save(update_fields=["status", "resolved_at"])
            self.asset.status = Asset.Status.AVAILABLE
            self.asset.save(update_fields=["status"])
            notify(self.raised_by, f"Maintenance on {self.asset} is resolved — asset is Available again.")


class AuditCycle(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=150)
    scope_department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    scope_location = models.CharField(max_length=150, blank=True)
    date_start = models.DateField()
    date_end = models.DateField()
    auditors = models.ManyToManyField(User, related_name="audit_cycles", blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_start"]

    def __str__(self):
        return self.name

    def in_scope_assets(self):
        qs = Asset.objects.exclude(status=Asset.Status.DISPOSED)
        if self.scope_department_id:
            qs = qs.filter(department_id=self.scope_department_id)
        if self.scope_location:
            qs = qs.filter(location__icontains=self.scope_location)
        return qs

    def ensure_items(self):
        """Create one AuditItem per in-scope asset that doesn't already
        have one for this cycle. Idempotent — safe to call every time the
        audit screen loads."""
        existing_ids = set(self.items.values_list("asset_id", flat=True))
        new_items = [
            AuditItem(audit_cycle=self, asset=asset)
            for asset in self.in_scope_assets() if asset.id not in existing_ids
        ]
        if new_items:
            AuditItem.objects.bulk_create(new_items)

    @property
    def discrepancies(self):
        return self.items.exclude(result=AuditItem.Result.VERIFIED).exclude(result=AuditItem.Result.PENDING)

    def close(self):
        """Locks the cycle and updates asset statuses: Missing ->
        Asset.Status.LOST, per the brief."""
        if self.status != self.Status.OPEN:
            raise ValidationError("This audit cycle is already closed.")
        with transaction.atomic():
            for item in self.items.filter(result=AuditItem.Result.MISSING):
                item.asset.status = Asset.Status.LOST
                item.asset.save(update_fields=["status"])
            self.status = self.Status.CLOSED
            self.closed_at = timezone.now()
            self.save(update_fields=["status", "closed_at"])
            for auditor in self.auditors.all():
                notify(auditor, f"Audit cycle '{self.name}' is closed.")


class AuditItem(models.Model):
    class Result(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        MISSING = "MISSING", "Missing"
        DAMAGED = "DAMAGED", "Damaged"

    audit_cycle = models.ForeignKey(AuditCycle, on_delete=models.CASCADE, related_name="items")
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="audit_items")
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.PENDING)
    notes = models.CharField(max_length=300, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["asset__asset_tag"]
        unique_together = [("audit_cycle", "asset")]

    def __str__(self):
        return f"{self.asset.asset_tag} — {self.result}"

    def mark(self, result, notes=""):
        self.result = result
        self.notes = notes
        self.checked_at = timezone.now()
        self.save(update_fields=["result", "notes", "checked_at"])
        if result in (self.Result.MISSING, self.Result.DAMAGED):
            for auditor in self.audit_cycle.auditors.all():
                notify(auditor, f"Discrepancy flagged: {self.asset} marked {result} in '{self.audit_cycle.name}'.")


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=300)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message


def notify(user, message):
    """Single choke point for creating notifications — every workflow
    method above calls this instead of creating Notification objects
    directly, so 'what triggers a notification' is answerable by
    grepping one function name. Silently no-ops if user is None (e.g. an
    allocation to a department with no specific employee)."""
    if user is None:
        return
    Notification.objects.create(user=user, message=message)


class ActivityLog(models.Model):
    """Lightweight audit trail: who did what, when. Call log_activity()
    explicitly at the point of action rather than wiring signals on every
    model — explicit call sites are easier for a hackathon team to reason
    about and extend than implicit signal handlers."""

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="activity_logs")
    description = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.description


def log_activity(user, description):
    ActivityLog.objects.create(user=user, description=description)
