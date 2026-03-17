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
    if not is_active_internal_user(user):
        return None
    return getattr(user, "operator_profile", None)


def active_assignment_q(now=None) -> Q:
    now = now or timezone.now()
    return Q(active=True) & Q(starts_at__lte=now) & (Q(ends_at__isnull=True) | Q(ends_at__gt=now))


def _none(qs: QuerySet) -> QuerySet:
    return qs.none()


def scope_creators_queryset(user, qs: Optional[QuerySet] = None) -> QuerySet:
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
    if not can_view_creator(user, creator):
        raise PermissionDenied("Creator is not in scope for this user.")
