"""core/mixins.py

Small, Django-CBV mixins to enforce Sprint 1–2 canon.
"""

from __future__ import annotations

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from core.authz import (
    is_active_internal_user,
    is_admin,
    require_creator_in_scope,
    scope_assignments_queryset,
    scope_channels_queryset,
    scope_creators_queryset,
)


class AdminOnlyMixin(AccessMixin):
    """Allow access only to active internal admin users."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not is_active_internal_user(user):
            return self.handle_no_permission()
        if not is_admin(user):
            raise PermissionDenied("Admin access required.")
        return super().dispatch(request, *args, **kwargs)


class ScopedCreatorQuerysetMixin(AccessMixin):
    """Apply creator scope to `get_queryset()` for non-admin users."""

    def get_queryset(self):
        qs = super().get_queryset()
        return scope_creators_queryset(self.request.user, qs=qs)


class ScopedChannelQuerysetMixin(AccessMixin):
    """Apply channel scope to `get_queryset()` for non-admin users."""

    def get_queryset(self):
        qs = super().get_queryset()
        return scope_channels_queryset(self.request.user, qs=qs)


class ScopedAssignmentQuerysetMixin(AccessMixin):
    """Apply assignment scope to `get_queryset()` for non-admin users."""

    def get_queryset(self):
        qs = super().get_queryset()
        return scope_assignments_queryset(self.request.user, qs=qs)


class ScopedCreatorObjectMixin(AccessMixin):
    """Guard a single Creator object (useful for DetailView)."""

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        require_creator_in_scope(self.request.user, obj)
        return obj
