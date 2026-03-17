"""core/authz.py

Sprint 1–2: small, explicit helpers for authorization and scope.

Canon:
- Admin: active internal user AND (`user.is_staff` or `user.is_superuser`)
- Active internal user: authenticated + active
- Operator identity: `user.operator_profile`
- Scope comes ONLY from active, valid OperatorAssignment windows.
"""

from __future__ import annotations

from typing import Optional

from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.utils import timezone

from core.models import Creator, CreatorChannel, Operator, OperatorAssignment


def is_active_internal_user(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "is_active", False))


def is_admin(user) -> bool:
    return bool(
        is_active_internal_user(user)
        and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    )


def get_operator_for_user(user) -> Optional[Operator]:
    """Return the Operator profile for this user, or None."""
    if not is_active_internal_user(user):
        return None
    return getattr(user, "operator_profile", None)


def active_assignment_q(now=None) -> Q:
    """Return a Q() for assignments that are active at `now`.

    Window semantics:
    - active if `starts_at <= now`
    - and (`ends_at` is NULL OR `ends_at > now`)  (end is exclusive)
    """
    now = now or timezone.now()
    return Q(starts_at__lte=now) & (Q(ends_at__isnull=True) | Q(ends_at__gt=now))


def _none(qs: QuerySet) -> QuerySet:
    return qs.none()


def scope_creators_queryset(user, qs: Optional[QuerySet] = None) -> QuerySet:
    """Return creators visible to `user` per Sprint 1–2 canon."""
    qs = qs if qs is not None else Creator.objects.all()

    if not is_active_internal_user(user):
        return _none(qs)

    if is_admin(user):
        return qs

    operator = get_operator_for_user(user)
    if operator is None:
        return _none(qs)

    now = timezone.now()
    creator_ids = (
        OperatorAssignment.objects.filter(operator=operator)
        .filter(active_assignment_q(now))
        .values_list("creator_id", flat=True)
    )
    return qs.filter(pk__in=creator_ids).distinct()


def scope_channels_queryset(user, qs: Optional[QuerySet] = None) -> QuerySet:
    """Return channels visible to `user` via creator scope."""
    qs = qs if qs is not None else CreatorChannel.objects.all()

    if not is_active_internal_user(user):
        return _none(qs)

    if is_admin(user):
        return qs

    operator = get_operator_for_user(user)
    if operator is None:
        return _none(qs)

    now = timezone.now()
    creator_ids = (
        OperatorAssignment.objects.filter(operator=operator)
        .filter(active_assignment_q(now))
        .values_list("creator_id", flat=True)
    )
    return qs.filter(creator_id__in=creator_ids).distinct()


def scope_assignments_queryset(user, qs: Optional[QuerySet] = None) -> QuerySet:
    """Return assignments visible to `user` (admin = all, operator = own active)."""
    qs = qs if qs is not None else OperatorAssignment.objects.all()

    if not is_active_internal_user(user):
        return _none(qs)

    if is_admin(user):
        return qs

    operator = get_operator_for_user(user)
    if operator is None:
        return _none(qs)

    now = timezone.now()
    return qs.filter(operator=operator).filter(active_assignment_q(now)).distinct()


def can_view_creator(user, creator: Creator) -> bool:
    """True iff `user` may view `creator` per assignment-based scope."""
    if not is_active_internal_user(user):
        return False
    if is_admin(user):
        return True

    operator = get_operator_for_user(user)
    if operator is None:
        return False

    now = timezone.now()
    return (
        OperatorAssignment.objects.filter(operator=operator, creator=creator)
        .filter(active_assignment_q(now))
        .exists()
    )


def require_creator_in_scope(user, creator: Creator) -> None:
    """Raise PermissionDenied if creator is out of scope."""
    if not can_view_creator(user, creator):
        raise PermissionDenied("Creator is not in scope for this user.")
