from django.db.models import Q
from django.utils import timezone

from core.models import Creator, CreatorChannel, OperatorAssignment


def _is_active_authenticated_user(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
    )


def is_admin_user(user):
    return bool(
        _is_active_authenticated_user(user)
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "is_staff", False)
        )
    )


def get_operator_for_user(user):
    if not _is_active_authenticated_user(user):
        return None
    return getattr(user, "operator_profile", None)


def get_active_assignments_queryset(operator=None):
    now = timezone.now()
    qs = (
        OperatorAssignment.objects
        .filter(active=True)
        .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    )

    if operator is not None:
        qs = qs.filter(operator=operator)

    return qs


def get_active_assignments_for_operator(operator):
    if operator is None:
        return OperatorAssignment.objects.none()
    return get_active_assignments_queryset(operator=operator)


def get_creator_queryset_for_user(user):
    if is_admin_user(user):
        return Creator.objects.all()

    operator = get_operator_for_user(user)
    if operator is None:
        return Creator.objects.none()

    creator_ids = get_active_assignments_for_operator(operator).values_list(
        "creator_id",
        flat=True,
    )
    return Creator.objects.filter(pk__in=creator_ids).distinct()


def get_channel_queryset_for_user(user):
    if is_admin_user(user):
        return CreatorChannel.objects.all()

    operator = get_operator_for_user(user)
    if operator is None:
        return CreatorChannel.objects.none()

    creator_ids = get_active_assignments_for_operator(operator).values_list(
        "creator_id",
        flat=True,
    )
    return CreatorChannel.objects.filter(creator_id__in=creator_ids).distinct()


def user_can_access_creator(user, creator):
    return get_creator_queryset_for_user(user).filter(pk=creator.pk).exists()


def user_can_access_channel(user, channel):
    return get_channel_queryset_for_user(user).filter(pk=channel.pk).exists()
