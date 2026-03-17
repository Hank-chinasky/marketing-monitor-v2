from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db.models import Q


def validate_active_creator_requires_active_consent(creator) -> None:
    status = getattr(creator, "status", None)
    consent_status = getattr(creator, "consent_status", None)

    if status == "active" and consent_status != "active":
        raise ValidationError(
            {"consent_status": "Creators with status=active require consent_status=active."}
        )


def validate_assignment_dates(assignment) -> None:
    starts_at = getattr(assignment, "starts_at", None)
    ends_at = getattr(assignment, "ends_at", None)

    if starts_at is None:
        raise ValidationError({"starts_at": "starts_at is required."})

    if ends_at is not None and ends_at <= starts_at:
        raise ValidationError({"ends_at": "ends_at must be later than starts_at."})


def validate_no_overlapping_assignments(assignment) -> None:
    if getattr(assignment, "creator_id", None) is None:
        raise ValidationError({"creator": "creator is required."})

    validate_assignment_dates(assignment)

    starts_at = assignment.starts_at
    ends_at = assignment.ends_at

    qs = assignment.__class__.objects.filter(creator_id=assignment.creator_id)
    if assignment.pk:
        qs = qs.exclude(pk=assignment.pk)

    left = Q() if ends_at is None else Q(starts_at__lt=ends_at)
    right = Q(ends_at__isnull=True) | Q(ends_at__gt=starts_at)

    if qs.filter(left & right).exists():
        raise ValidationError(
            "Overlapping assignment windows for the same creator are not allowed (across any operators)."
        )


def validate_platform_handle_unique_ci(channel) -> None:
    platform = getattr(channel, "platform", None)
    handle = getattr(channel, "handle", None)

    if not platform:
        raise ValidationError({"platform": "platform is required."})
    if not handle:
        raise ValidationError({"handle": "handle is required."})

    qs = channel.__class__.objects.filter(platform=platform, handle__iexact=handle)
    if channel.pk:
        qs = qs.exclude(pk=channel.pk)

    if qs.exists():
        raise ValidationError(
            {"handle": "This handle already exists for this platform (case-insensitive)."}
        )
