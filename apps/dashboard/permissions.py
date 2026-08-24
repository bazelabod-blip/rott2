from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator


def can_access_dashboard(user):
    return bool(user.is_authenticated and user.is_active and (user.is_staff or user.is_superuser or getattr(user, 'role', '') in {'admin', 'super_admin'}))


def dashboard_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not can_access_dashboard(request.user):
            raise PermissionDenied('ليست لديك صلاحية الدخول إلى لوحة التحكم.')
        return view_func(request, *args, **kwargs)
    return _wrapped


class DashboardAccessMixin:
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not can_access_dashboard(request.user):
            raise PermissionDenied('ليست لديك صلاحية الدخول إلى لوحة التحكم.')
        return super().dispatch(request, *args, **kwargs)
