import csv

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import role_required
from .forms import (AllocateForm, AssetCategoryForm, AssetForm, AuditCycleForm,
                     AuditItemMarkForm, BookingForm, DepartmentForm,
                     MaintenanceRequestForm, PromoteForm, ReturnForm, SignupForm,
                     TechnicianAssignForm, TransferRequestForm)
from .models import (ActivityLog, Allocation, Asset, AssetCategory, AuditCycle,
                      AuditItem, Booking, Department, MaintenanceRequest,
                      Notification, TransferRequest, User, log_activity)

MANAGES_ORG = ("ADMIN",)
MANAGES_ASSETS = ("ASSET_MANAGER", "ADMIN")
APPROVES_TRANSFERS = ("ASSET_MANAGER", "DEPARTMENT_HEAD", "ADMIN")
APPROVES_MAINTENANCE = ("ASSET_MANAGER", "ADMIN")
MANAGES_AUDITS = ("ASSET_MANAGER", "ADMIN")


# --- Auth ----------------------------------------------------------------

def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.EMPLOYEE  # forced — see SignupForm docstring
            user.save()
            login(request, user)
            messages.success(request, "Account created as Employee. An Admin can promote you later if needed.")
            return redirect("dashboard")
    else:
        form = SignupForm()
    return render(request, "core/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username", ""),
                             password=request.POST.get("password", ""))
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# --- Dashboard -------------------------------------------------------------

@login_required(login_url="login")
def dashboard(request):
    today = timezone.localdate()
    kpis = {
        "available": Asset.objects.filter(status=Asset.Status.AVAILABLE).count(),
        "allocated": Asset.objects.filter(status=Asset.Status.ALLOCATED).count(),
        "maintenance_today": MaintenanceRequest.objects.filter(
            status__in=[MaintenanceRequest.Status.APPROVED, MaintenanceRequest.Status.IN_PROGRESS,
                        MaintenanceRequest.Status.TECHNICIAN_ASSIGNED],
        ).count(),
        "active_bookings": Booking.objects.filter(is_cancelled=False, end_time__gte=timezone.now()).count(),
        "pending_transfers": TransferRequest.objects.filter(status=TransferRequest.Status.REQUESTED).count(),
    }
    overdue = Allocation.objects.filter(
        status=Allocation.Status.ACTIVE, expected_return_date__lt=today
    ).select_related("asset", "employee")
    upcoming_returns = Allocation.objects.filter(
        status=Allocation.Status.ACTIVE, expected_return_date__gte=today
    ).exclude(expected_return_date=None).select_related("asset", "employee")[:8]
    kpis["upcoming_returns"] = upcoming_returns.count()

    recent_activity = ActivityLog.objects.select_related("user")[:10]
    unread_notifications = request.user.notifications.filter(is_read=False)[:5]

    return render(request, "core/dashboard.html", {
        "kpis": kpis, "overdue": overdue, "upcoming_returns": upcoming_returns,
        "recent_activity": recent_activity, "unread_notifications": unread_notifications,
    })


# --- Org setup (Admin only) -------------------------------------------------

@login_required(login_url="login")
def org_setup(request):
    return render(request, "core/org_setup.html", {
        "departments": Department.objects.all(),
        "categories": AssetCategory.objects.all(),
        "employees": User.objects.all(),
        "can_manage": request.user.has_role(*MANAGES_ORG),
    })


@role_required(*MANAGES_ORG)
def department_form(request, pk=None):
    dept = get_object_or_404(Department, pk=pk) if pk else None
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            log_activity(request.user, f"{'Updated' if dept else 'Created'} department {form.instance.name}")
            messages.success(request, "Department saved.")
            return redirect("org_setup")
    else:
        form = DepartmentForm(instance=dept)
    return render(request, "core/simple_form.html", {"form": form, "title": "Department", "back_url": "org_setup"})


@role_required(*MANAGES_ORG)
def category_form(request, pk=None):
    category = get_object_or_404(AssetCategory, pk=pk) if pk else None
    if request.method == "POST":
        form = AssetCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Asset category saved.")
            return redirect("org_setup")
    else:
        form = AssetCategoryForm(instance=category)
    return render(request, "core/simple_form.html", {"form": form, "title": "Asset category", "back_url": "org_setup"})


@role_required(*MANAGES_ORG)
def promote_employee(request, pk):
    """The ONLY place a role changes after signup — see SignupForm and
    PromoteForm docstrings. Admin-gated via @role_required("ADMIN")."""
    employee = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = PromoteForm(request.POST)
        if form.is_valid():
            employee.role = form.cleaned_data["role"]
            if form.cleaned_data.get("department"):
                employee.department = form.cleaned_data["department"]
            employee.save(update_fields=["role", "department"])
            log_activity(request.user, f"Promoted {employee} to {employee.get_role_display()}")
            messages.success(request, f"{employee} is now {employee.get_role_display()}.")
            return redirect("org_setup")
    else:
        form = PromoteForm(initial={"department": employee.department_id})
    return render(request, "core/promote_form.html", {"form": form, "employee": employee})


# --- Assets ------------------------------------------------------------------

@login_required(login_url="login")
def asset_list(request):
    assets = Asset.objects.select_related("category", "department")
    q = request.GET.get("q")
    status = request.GET.get("status")
    category = request.GET.get("category")
    if q:
        assets = assets.filter(
            Q(asset_tag__icontains=q) | Q(serial_number__icontains=q) | Q(name__icontains=q)
        )
    if status:
        assets = assets.filter(status=status)
    if category:
        assets = assets.filter(category_id=category)
    return render(request, "core/asset_list.html", {
        "assets": assets.distinct(), "statuses": Asset.Status.choices,
        "categories": AssetCategory.objects.all(),
        "can_manage": request.user.has_role(*MANAGES_ASSETS),
    })


@role_required(*MANAGES_ASSETS)
def asset_form(request, pk=None):
    asset = get_object_or_404(Asset, pk=pk) if pk else None
    if request.method == "POST":
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            is_new = asset is None
            obj = form.save()
            log_activity(request.user, f"{'Registered' if is_new else 'Updated'} asset {obj.asset_tag}")
            messages.success(request, f"Asset {obj.asset_tag} saved.")
            return redirect("asset_detail", pk=obj.pk)
    else:
        form = AssetForm(instance=asset)
    return render(request, "core/asset_form.html", {"form": form, "asset": asset})


@login_required(login_url="login")
def asset_detail(request, pk):
    asset = get_object_or_404(Asset.objects.select_related("category", "department"), pk=pk)
    allocate_form = AllocateForm()
    transfer_form = TransferRequestForm()
    return render(request, "core/asset_detail.html", {
        "asset": asset,
        "allocations": asset.allocations.select_related("employee", "department")[:10],
        "maintenance_requests": asset.maintenance_requests.select_related("raised_by")[:10],
        "current_allocation": asset.current_allocation,
        "allocate_form": allocate_form,
        "transfer_form": transfer_form,
        "can_manage": request.user.has_role(*MANAGES_ASSETS),
        "can_approve_transfer": request.user.has_role(*APPROVES_TRANSFERS),
    })


# --- Allocation & Transfer ---------------------------------------------------

@role_required(*MANAGES_ASSETS)
def asset_allocate(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        form = AllocateForm(request.POST)
        if form.is_valid():
            try:
                Allocation.create_for(
                    asset, employee=form.cleaned_data.get("employee"),
                    department=form.cleaned_data.get("department"),
                    expected_return_date=form.cleaned_data.get("expected_return_date"),
                )
                log_activity(request.user, f"Allocated {asset.asset_tag}")
                messages.success(request, f"{asset} allocated.")
            except ValidationError as e:
                messages.error(request, "; ".join(e.messages))
    return redirect("asset_detail", pk=pk)


@login_required(login_url="login")
def transfer_request_create(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        form = TransferRequestForm(request.POST)
        if form.is_valid():
            TransferRequest.objects.create(
                asset=asset, requested_by=request.user,
                to_employee=form.cleaned_data.get("to_employee"),
                to_department=form.cleaned_data.get("to_department"),
            )
            log_activity(request.user, f"Requested transfer of {asset.asset_tag}")
            messages.success(request, "Transfer requested — pending approval.")
    return redirect("asset_detail", pk=pk)


@role_required(*APPROVES_TRANSFERS)
def transfer_decide(request, pk, decision):
    transfer = get_object_or_404(TransferRequest, pk=pk)
    if request.method == "POST":
        try:
            if decision == "approve":
                transfer.approve(decided_by=request.user)
                messages.success(request, "Transfer approved.")
            else:
                transfer.reject(decided_by=request.user)
                messages.success(request, "Transfer rejected.")
            log_activity(request.user, f"{decision.title()}d transfer #{transfer.pk}")
        except ValidationError as e:
            messages.error(request, "; ".join(e.messages))
    return redirect("transfer_list")


@login_required(login_url="login")
def transfer_list(request):
    transfers = TransferRequest.objects.select_related("asset", "to_employee", "to_department", "requested_by")
    assets = Asset.objects.select_related("category", "department").all()
    employees = User.objects.filter(status="ACTIVE").order_by("first_name", "last_name")
    departments = Department.objects.filter(status="ACTIVE").order_by("name")
    return render(request, "core/transfer_list.html", {
        "transfers": transfers,
        "can_approve": request.user.has_role(*APPROVES_TRANSFERS),
        "assets": assets,
        "employees": employees,
        "departments": departments,
        "can_manage": request.user.has_role(*MANAGES_ASSETS),
    })


@role_required(*MANAGES_ASSETS)
def allocation_return(request, pk):
    allocation = get_object_or_404(Allocation, pk=pk)
    if request.method == "POST":
        form = ReturnForm(request.POST)
        if form.is_valid():
            try:
                allocation.mark_returned(condition_notes=form.cleaned_data.get("condition_notes", ""))
                log_activity(request.user, f"Returned {allocation.asset.asset_tag}")
                messages.success(request, "Marked returned — asset is Available.")
            except ValidationError as e:
                messages.error(request, "; ".join(e.messages))
    return redirect("asset_detail", pk=allocation.asset_id)


# --- Booking -----------------------------------------------------------------

@login_required(login_url="login")
def booking_list(request):
    bookings = Booking.objects.select_related("asset", "booked_by")
    asset_id = request.GET.get("asset")
    if asset_id:
        bookings = bookings.filter(asset_id=asset_id)
    return render(request, "core/booking_list.html", {
        "bookings": bookings, "bookable_assets": Asset.objects.filter(is_bookable=True),
    })


@login_required(login_url="login")
def booking_create(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                Booking.create_for(
                    form.cleaned_data["asset"], request.user,
                    form.cleaned_data["start_time"], form.cleaned_data["end_time"],
                )
                log_activity(request.user, f"Booked {form.cleaned_data['asset'].asset_tag}")
                messages.success(request, "Booking confirmed.")
                return redirect("booking_list")
            except ValidationError as e:
                form.add_error(None, "; ".join(e.messages))
    else:
        form = BookingForm()
    return render(request, "core/booking_form.html", {"form": form})


@login_required(login_url="login")
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST" and (booking.booked_by_id == request.user.id or request.user.has_role(*MANAGES_ASSETS)):
        booking.cancel()
        messages.success(request, "Booking cancelled.")
    return redirect("booking_list")


# --- Maintenance ---------------------------------------------------------

@login_required(login_url="login")
def maintenance_list(request):
    requests_qs = MaintenanceRequest.objects.select_related("asset", "raised_by")
    return render(request, "core/maintenance_list.html", {
        "requests": requests_qs, "can_approve": request.user.has_role(*APPROVES_MAINTENANCE),
    })


@login_required(login_url="login")
def maintenance_create(request):
    if request.method == "POST":
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.raised_by = request.user
            req.save()
            log_activity(request.user, f"Raised maintenance request for {req.asset.asset_tag}")
            messages.success(request, "Maintenance request raised — pending approval.")
            return redirect("maintenance_list")
    else:
        form = MaintenanceRequestForm()
    return render(request, "core/maintenance_form.html", {"form": form})


@role_required(*APPROVES_MAINTENANCE)
def maintenance_decide(request, pk, decision):
    req = get_object_or_404(MaintenanceRequest, pk=pk)
    if request.method == "POST":
        try:
            if decision == "approve":
                req.approve(decided_by=request.user)
                messages.success(request, "Approved — asset moved to Under Maintenance.")
            else:
                req.reject(decided_by=request.user)
                messages.success(request, "Rejected.")
        except ValidationError as e:
            messages.error(request, "; ".join(e.messages))
    return redirect("maintenance_list")


@role_required(*APPROVES_MAINTENANCE)
def maintenance_assign(request, pk):
    req = get_object_or_404(MaintenanceRequest, pk=pk)
    if request.method == "POST":
        form = TechnicianAssignForm(request.POST)
        if form.is_valid():
            try:
                req.assign_technician(form.cleaned_data["technician_name"])
                messages.success(request, "Technician assigned.")
            except ValidationError as e:
                messages.error(request, "; ".join(e.messages))
    return redirect("maintenance_list")


@role_required(*APPROVES_MAINTENANCE)
def maintenance_start(request, pk):
    req = get_object_or_404(MaintenanceRequest, pk=pk)
    if request.method == "POST":
        try:
            req.start_progress()
            messages.success(request, "Marked In Progress.")
        except ValidationError as e:
            messages.error(request, "; ".join(e.messages))
    return redirect("maintenance_list")


@role_required(*APPROVES_MAINTENANCE)
def maintenance_resolve(request, pk):
    req = get_object_or_404(MaintenanceRequest, pk=pk)
    if request.method == "POST":
        try:
            req.resolve()
            log_activity(request.user, f"Resolved maintenance for {req.asset.asset_tag}")
            messages.success(request, "Resolved — asset is Available again.")
        except ValidationError as e:
            messages.error(request, "; ".join(e.messages))
    return redirect("maintenance_list")


# --- Audit -------------------------------------------------------------------

@login_required(login_url="login")
def audit_list(request):
    return render(request, "core/audit_list.html", {
        "cycles": AuditCycle.objects.all(), "can_manage": request.user.has_role(*MANAGES_AUDITS),
    })


@role_required(*MANAGES_AUDITS)
def audit_create(request):
    if request.method == "POST":
        form = AuditCycleForm(request.POST)
        if form.is_valid():
            cycle = form.save()
            cycle.ensure_items()
            log_activity(request.user, f"Created audit cycle {cycle.name}")
            messages.success(request, "Audit cycle created.")
            return redirect("audit_detail", pk=cycle.pk)
    else:
        form = AuditCycleForm()
    return render(request, "core/audit_form.html", {"form": form})


@login_required(login_url="login")
def audit_detail(request, pk):
    cycle = get_object_or_404(AuditCycle, pk=pk)
    is_auditor = request.user in cycle.auditors.all()
    cycle.ensure_items()
    return render(request, "core/audit_detail.html", {
        "cycle": cycle, "items": cycle.items.select_related("asset"),
        "discrepancies": cycle.discrepancies.select_related("asset"),
        "can_mark": is_auditor or request.user.has_role(*MANAGES_AUDITS),
        "can_close": request.user.has_role(*MANAGES_AUDITS),
        "mark_form": AuditItemMarkForm(),
    })


@login_required(login_url="login")
def audit_item_mark(request, pk):
    item = get_object_or_404(AuditItem, pk=pk)
    is_auditor = request.user in item.audit_cycle.auditors.all()
    if not (is_auditor or request.user.has_role(*MANAGES_AUDITS)):
        messages.error(request, "You're not an auditor on this cycle.")
        return redirect("audit_detail", pk=item.audit_cycle_id)
    if request.method == "POST":
        form = AuditItemMarkForm(request.POST)
        if form.is_valid():
            item.mark(form.cleaned_data["result"], form.cleaned_data.get("notes", ""))
    return redirect("audit_detail", pk=item.audit_cycle_id)


@role_required(*MANAGES_AUDITS)
def audit_close(request, pk):
    cycle = get_object_or_404(AuditCycle, pk=pk)
    if request.method == "POST":
        try:
            cycle.close()
            log_activity(request.user, f"Closed audit cycle {cycle.name}")
            messages.success(request, "Audit cycle closed.")
        except ValidationError as e:
            messages.error(request, "; ".join(e.messages))
    return redirect("audit_detail", pk=pk)


# --- Reports -----------------------------------------------------------------

@login_required(login_url="login")
def reports(request):
    assets = Asset.objects.select_related("category", "department")
    by_category = {}
    for a in assets:
        by_category.setdefault(a.category.name, {"total": 0, "allocated": 0})
        by_category[a.category.name]["total"] += 1
        if a.status == Asset.Status.ALLOCATED:
            by_category[a.category.name]["allocated"] += 1

    by_department = {}
    for a in assets.exclude(department=None):
        by_department.setdefault(a.department.name, 0)
        by_department[a.department.name] += 1

    nearing_retirement = assets.filter(status=Asset.Status.AVAILABLE).order_by("acquisition_date")[:10]
    maintenance_counts = {}
    for req in MaintenanceRequest.objects.select_related("asset"):
        maintenance_counts.setdefault(req.asset.asset_tag, 0)
        maintenance_counts[req.asset.asset_tag] += 1
    most_maintained = sorted(maintenance_counts.items(), key=lambda kv: -kv[1])[:10]

    return render(request, "core/reports.html", {
        "by_category": by_category, "by_department": by_department,
        "nearing_retirement": nearing_retirement, "most_maintained": most_maintained,
    })


@login_required(login_url="login")
def reports_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="assetflow_report.csv"'
    writer = csv.writer(response)
    writer.writerow(["Tag", "Name", "Category", "Status", "Department", "Location",
                      "Acquisition cost", "Acquisition date", "Bookable"])
    for a in Asset.objects.select_related("category", "department"):
        writer.writerow([a.asset_tag, a.name, a.category.name, a.get_status_display(),
                          a.department.name if a.department else "", a.location,
                          a.acquisition_cost, a.acquisition_date, a.is_bookable])
    return response


# --- Notifications & activity log -----------------------------------------

@login_required(login_url="login")
def notification_list(request):
    notifications = request.user.notifications.all()
    return render(request, "core/notification_list.html", {"notifications": notifications})


@login_required(login_url="login")
def notification_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return redirect("notification_list")


@login_required(login_url="login")
def activity_log(request):
    return render(request, "core/activity_log.html", {"logs": ActivityLog.objects.select_related("user")[:200]})
