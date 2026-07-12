from django import template

register = template.Library()

_PILL_MAP = {
    "AVAILABLE": "pill-ok", "ALLOCATED": "pill-info", "RESERVED": "pill-info",
    "UNDER_MAINTENANCE": "pill-warn", "LOST": "pill-danger", "RETIRED": "pill-muted",
    "DISPOSED": "pill-muted", "ACTIVE": "pill-ok", "INACTIVE": "pill-muted",
    "RETURNED": "pill-muted", "REQUESTED": "pill-warn", "APPROVED": "pill-ok",
    "REJECTED": "pill-danger", "UPCOMING": "pill-info", "ONGOING": "pill-ok",
    "COMPLETED": "pill-muted", "CANCELLED": "pill-danger", "PENDING": "pill-warn",
    "TECHNICIAN_ASSIGNED": "pill-info", "IN_PROGRESS": "pill-info", "RESOLVED": "pill-ok",
    "OPEN": "pill-warn", "CLOSED": "pill-muted", "VERIFIED": "pill-ok",
    "MISSING": "pill-danger", "DAMAGED": "pill-warn",
}


@register.filter
def status_pill(value):
    return _PILL_MAP.get(value, "pill-muted")
