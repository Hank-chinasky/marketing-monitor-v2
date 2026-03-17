"""core/validators.py

Sprint 1–2 validation helpers.
Use from Django forms or `Model.clean()`.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db.models import Q

from core.models import CreatorChannel, OperatorAssignment


def validate_active_creator_requires_active_consent(creator) -> None:
    """If a creator is operationally active, consent must be active.

    Expected fields:
    - `creator.status` (str), with 'active' meaning operationally active
    - `creator.consent_status` (str), with 'active' meaning active consent
    """
    status = getattr(creator, "status", None)
    consent_status = getattr(creator, "consent_status", None)

    if status == "active" and consent_status != "active":
        raise ValidationError({"consent_status": "Creators with status=active require consent_status=active."})


def validate_assignment_dates(assignment) -> None:
    """Validate assignment dates.

    Canon rule:
    - `ends_at` may be NULL (open-ended)
    - If set: `ends_at` must be strictly greater than `starts_at`
    """
    starts_at = getattr(assignment, "starts_at", None)
    ends_at = getattr(assignment, "ends_at", None)

    if starts_at is None:
        raise ValidationError({"starts_at": "starts_at is required."})

    if ends_at is not None and ends_at <= starts_at:
        raise ValidationError({"ends_at": "ends_at must be later than starts_at."})


def validate_no_overlapping_assignments(assignment) -> None:
    """Block overlapping assignments for the same creator.

    Canon (Sprint 1–2):
    - A creator must NOT have overlapping assignment windows, even across different operators.
    - This keeps scope deterministic and prevents accidental multi-operator scope overlap.
    """
    if getattr(assignment, "creator_id", None) is None:
        raise ValidationError({"creator": "creator is required."})

    validate_assignment_dates(assignment)

    starts_at = assignment.starts_at
    ends_at = assignment.ends_at

    qs = OperatorAssignment.objects.filter(creator_id=assignment.creator_id)
    if assignment.pk:
        qs = qs.exclude(pk=assignment.pk)

    # Overlap test (end exclusive):
    # existing overlaps new if:
    #   existing.starts_at < new_end (or new_end is open)
    #   and existing_end > new_start (or existing_end is open)
    if ends_at is None:
        left = Q()
    else:
        left = Q(starts_at__lt=ends_at)

    right = Q(ends_at__isnull=True) | Q(ends_at__gt=starts_at)

    if qs.filter(left & right).exists():
        raise ValidationError("Overlapping assignment windows for the same creator are not allowed (across any operators).")


def validate_platform_handle_unique_ci(channel: CreatorChannel) -> None:
    """App-level fallback: prevent case-insensitive duplicates for (platform, handle).

    Canon:
    - enforce (platform, handle) uniqueness case-insensitively at app level
    - DB-level enforcement may follow later (e.g. PostgreSQL functional index)
    """
    platform = getattr(channel, "platform", None)
    handle = getattr(channel, "handle", None)

    if not platform:
        raise ValidationError({"platform": "platform is required."})
    if not handle:
        raise ValidationError({"handle": "handle is required."})

    qs = CreatorChannel.objects.filter(platform=platform, handle__iexact=handle)
    if channel.pk:
        qs = qs.exclude(pk=channel.pk)

    if qs.exists():
        raise ValidationError({"handle": "This handle already exists for this platform (case-insensitive)."})
