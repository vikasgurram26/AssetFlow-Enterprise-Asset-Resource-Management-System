from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (ActivityLog, Allocation, Asset, AssetCategory, AuditCycle,
                      AuditItem, Booking, Department, MaintenanceRequest,
                      Notification, TransferRequest, User)


@admin.register(User)
class AssetFlowUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role", "department", "status")}),)
    list_display = ("username", "email", "role", "department", "is_staff")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "head", "parent", "status")


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "warranty_period_days")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("asset_tag", "name", "category", "status", "department", "is_bookable")
    list_filter = ("status", "category", "is_bookable")
    search_fields = ("asset_tag", "name", "serial_number")


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ("asset", "employee", "department", "status", "allocated_date", "expected_return_date")
    list_filter = ("status",)


@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    list_display = ("asset", "to_employee", "to_department", "status", "requested_at")
    list_filter = ("status",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("asset", "booked_by", "start_time", "end_time", "is_cancelled")


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ("asset", "raised_by", "priority", "status", "created_at")
    list_filter = ("status", "priority")


@admin.register(AuditCycle)
class AuditCycleAdmin(admin.ModelAdmin):
    list_display = ("name", "date_start", "date_end", "status")
    filter_horizontal = ("auditors",)


@admin.register(AuditItem)
class AuditItemAdmin(admin.ModelAdmin):
    list_display = ("audit_cycle", "asset", "result", "checked_at")
    list_filter = ("result",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "description", "created_at")
