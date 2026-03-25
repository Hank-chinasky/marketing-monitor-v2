from __future__ import annotations

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from core.services.scope import (
    get_active_assignments_for_operator,
    get_channel_queryset_for_user,
    get_creator_queryset_for_user,
    get_operator_for_user,
    is_admin_user,
)


class AdminOnlyMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            raise PermissionDenied("Admin access required.")
        return super().dispatch(request, *args, **kwargs)


class AdminDeleteOnlyMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            raise PermissionDenied("Admin access required.")
        return super().dispatch(request, *args, **kwargs)


class ScopedCreatorQuerysetMixin(AccessMixin):
    def get_queryset(self):
        base_qs = super().get_queryset()
        scoped_qs = get_creator_queryset_for_user(self.request.user)
        return base_qs.filter(pk__in=scoped_qs.values("pk"))


class ScopedChannelQuerysetMixin(AccessMixin):
    def get_queryset(self):
        base_qs = super().get_queryset()
        scoped_qs = get_channel_queryset_for_user(self.request.user)
        return base_qs.filter(pk__in=scoped_qs.values("pk"))


class ScopedAssignmentQuerysetMixin(AccessMixin):
    def get_queryset(self):
        base_qs = super().get_queryset()

        if is_admin_user(self.request.user):
            return base_qs

        operator = get_operator_for_user(self.request.user)
        if operator is None:
            return base_qs.none()

        scoped_qs = get_active_assignments_for_operator(operator)
        return base_qs.filter(pk__in=scoped_qs.values("pk"))
