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
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not is_active_internal_user(user):
            return self.handle_no_permission()
        if not is_admin(user):
            raise PermissionDenied("Admin access required.")
        return super().dispatch(request, *args, **kwargs)


class ScopedCreatorQuerysetMixin(AccessMixin):
    def get_queryset(self):
        return scope_creators_queryset(self.request.user, qs=super().get_queryset())


class ScopedChannelQuerysetMixin(AccessMixin):
    def get_queryset(self):
        return scope_channels_queryset(self.request.user, qs=super().get_queryset())


class ScopedAssignmentQuerysetMixin(AccessMixin):
    def get_queryset(self):
        return scope_assignments_queryset(self.request.user, qs=super().get_queryset())


class ScopedCreatorObjectMixin(AccessMixin):
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        require_creator_in_scope(self.request.user, obj)
        return obj
