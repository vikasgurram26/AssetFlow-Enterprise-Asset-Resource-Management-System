from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """Restrict a view to specific User.Role values. Pass "ADMIN" to mean
    "is_staff/is_superuser OR role==ADMIN" (see User.has_role)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url="login")
        def wrapped(request, *args, **kwargs):
            if not request.user.has_role(*allowed_roles):
                messages.error(request, "You don't have permission to do that.")
                return redirect("dashboard")
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
