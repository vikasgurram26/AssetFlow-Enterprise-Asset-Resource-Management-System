from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),

    path("org/", views.org_setup, name="org_setup"),
    path("org/departments/new/", views.department_form, name="department_create"),
    path("org/departments/<int:pk>/edit/", views.department_form, name="department_edit"),
    path("org/categories/new/", views.category_form, name="category_create"),
    path("org/categories/<int:pk>/edit/", views.category_form, name="category_edit"),
    path("org/employees/<int:pk>/promote/", views.promote_employee, name="promote_employee"),

    path("assets/", views.asset_list, name="asset_list"),
    path("assets/bulk-retire/", views.asset_bulk_retire, name="asset_bulk_retire"),
    path("assets/new/", views.asset_form, name="asset_create"),
    path("assets/<int:pk>/", views.asset_detail, name="asset_detail"),
    path("assets/<int:pk>/edit/", views.asset_form, name="asset_edit"),
    path("assets/<int:pk>/allocate/", views.asset_allocate, name="asset_allocate"),
    path("assets/<int:pk>/transfer-request/", views.transfer_request_create, name="transfer_request_create"),

    path("transfers/", views.transfer_list, name="transfer_list"),
    path("transfers/<int:pk>/<str:decision>/", views.transfer_decide, name="transfer_decide"),

    path("allocations/<int:pk>/return/", views.allocation_return, name="allocation_return"),

    path("bookings/", views.booking_list, name="booking_list"),
    path("bookings/new/", views.booking_create, name="booking_create"),
    path("bookings/<int:pk>/cancel/", views.booking_cancel, name="booking_cancel"),

    path("maintenance/", views.maintenance_list, name="maintenance_list"),
    path("maintenance/new/", views.maintenance_create, name="maintenance_create"),
    # These three specific literal paths MUST come before the <str:decision>
    # wildcard below — Django resolves URLs in list order, and
    # <str:decision> matches "assign"/"start"/"resolve" as a decision
    # string too, silently routing those requests into maintenance_decide
    # (and from there into its reject() branch) instead of their own
    # views. Found this the hard way via end-to-end testing — see the
    # matching note in the project's test notes / commit history if you
    # add more maintenance sub-actions later, keep the specific ones above
    # the wildcard.
    path("maintenance/<int:pk>/assign/", views.maintenance_assign, name="maintenance_assign"),
    path("maintenance/<int:pk>/start/", views.maintenance_start, name="maintenance_start"),
    path("maintenance/<int:pk>/resolve/", views.maintenance_resolve, name="maintenance_resolve"),
    path("maintenance/<int:pk>/<str:decision>/", views.maintenance_decide, name="maintenance_decide"),

    path("audits/", views.audit_list, name="audit_list"),
    path("audits/new/", views.audit_create, name="audit_create"),
    path("audits/<int:pk>/", views.audit_detail, name="audit_detail"),
    path("audits/<int:pk>/close/", views.audit_close, name="audit_close"),
    path("audit-items/<int:pk>/mark/", views.audit_item_mark, name="audit_item_mark"),

    path("reports/", views.reports, name="reports"),
    path("reports/export.csv", views.reports_csv, name="reports_csv"),

    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/<int:pk>/read/", views.notification_read, name="notification_read"),
    path("activity-log/", views.activity_log, name="activity_log"),
]
