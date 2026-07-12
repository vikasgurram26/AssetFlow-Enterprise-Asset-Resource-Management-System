from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import (Asset, AssetCategory, AuditCycle, Booking, Department,
                      MaintenanceRequest, User)


def _bootstrapify(form):
    for name, field in form.fields.items():
        css = "form-select" if isinstance(field.widget, (forms.Select, forms.SelectMultiple)) else "form-control"
        field.widget.attrs.setdefault("class", css)


class SignupForm(UserCreationForm):
    """Public signup. Deliberately has NO role field — every account
    created here is forced to Role.EMPLOYEE in views.signup, regardless
    of what's posted. Don't add a role widget to this form; that would
    reopen the self-elevation hole the brief explicitly calls out."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "head", "parent", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["head"].queryset = User.objects.filter(role__in=[User.Role.DEPARTMENT_HEAD, User.Role.ADMIN])
        _bootstrapify(self)


class AssetCategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        fields = ["name", "description", "warranty_period_days"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class PromoteForm(forms.Form):
    """Admin-only. The ONLY place a role is assigned after signup — see
    the note on views.promote_employee."""
    role = forms.ChoiceField(choices=[
        (User.Role.DEPARTMENT_HEAD, "Department Head"),
        (User.Role.ASSET_MANAGER, "Asset Manager"),
        (User.Role.EMPLOYEE, "Employee (revoke elevated role)"),
    ])
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["name", "category", "serial_number", "acquisition_date", "acquisition_cost",
                  "condition", "location", "is_bookable", "department", "status"]
        widgets = {"acquisition_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class AllocateForm(forms.Form):
    """Allocate to an employee OR a department (not both). The queryset
    only needs active employees/departments — Allocation.create_for()
    does the real "already allocated" conflict check, this just keeps
    the dropdowns sane."""
    employee = forms.ModelChoiceField(queryset=User.objects.filter(status="ACTIVE"), required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.filter(status="ACTIVE"), required=False)
    expected_return_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("employee") and not cleaned.get("department"):
            raise forms.ValidationError("Choose an employee or a department to allocate to.")
        return cleaned


class TransferRequestForm(forms.Form):
    to_employee = forms.ModelChoiceField(queryset=User.objects.filter(status="ACTIVE"), required=False)
    to_department = forms.ModelChoiceField(queryset=Department.objects.filter(status="ACTIVE"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("to_employee") and not cleaned.get("to_department"):
            raise forms.ValidationError("Choose a destination employee or department.")
        return cleaned


class ReturnForm(forms.Form):
    condition_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class BookingForm(forms.Form):
    asset = forms.ModelChoiceField(queryset=Asset.objects.filter(is_bookable=True).exclude(
        status__in=[Asset.Status.RETIRED, Asset.Status.DISPOSED, Asset.Status.LOST]))
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ["asset", "issue_description", "priority"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Can't raise a request on something already being worked on /
        # disposed of — keep the dropdown to assets that are actually in
        # a state where "something's wrong with it" makes sense.
        self.fields["asset"].queryset = Asset.objects.exclude(
            status__in=[Asset.Status.UNDER_MAINTENANCE, Asset.Status.RETIRED,
                        Asset.Status.DISPOSED, Asset.Status.LOST]
        )
        _bootstrapify(self)


class TechnicianAssignForm(forms.Form):
    technician_name = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class AuditCycleForm(forms.ModelForm):
    class Meta:
        model = AuditCycle
        fields = ["name", "scope_department", "scope_location", "date_start", "date_end", "auditors"]
        widgets = {
            "date_start": forms.DateInput(attrs={"type": "date"}),
            "date_end": forms.DateInput(attrs={"type": "date"}),
            "auditors": forms.SelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class AuditItemMarkForm(forms.Form):
    result = forms.ChoiceField(choices=[("VERIFIED", "Verified"), ("MISSING", "Missing"), ("DAMAGED", "Damaged")])
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)
