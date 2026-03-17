from django.conf import settings
from django.db import models

from core.validators import (
    validate_active_creator_requires_active_consent,
    validate_no_overlapping_assignments,
    validate_platform_handle_unique_ci,
)


class Operator(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="operator_profile",
    )

    def __str__(self) -> str:
        full_name = self.user.get_full_name().strip()
        return full_name or self.user.username


class Creator(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        OFFBOARDED = "offboarded", "Offboarded"

    class ConsentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        REVOKED = "revoked", "Revoked"

    display_name = models.CharField(max_length=160)
    legal_name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    consent_status = models.CharField(max_length=20, choices=ConsentStatus.choices)
    primary_operator = models.ForeignKey(
        "Operator",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_creators",
    )
    notes = models.TextField(blank=True)

    def clean(self):
        validate_active_creator_requires_active_consent(self)

    def __str__(self) -> str:
        return self.display_name


class CreatorChannel(models.Model):
    class Platform(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        TIKTOK = "tiktok", "TikTok"
        TELEGRAM = "telegram", "Telegram"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        RESTRICTED = "restricted", "Restricted"
        BANNED = "banned", "Banned"

    class AccessMode(models.TextChoices):
        CREATOR_ONLY = "creator_only", "Creator only"
        OPERATOR_WITH_APPROVAL = "operator_with_approval", "Operator with approval"
        OPERATOR_DIRECT = "operator_direct", "Operator direct"
        DRAFT_ONLY = "draft_only", "Draft only"

    class RecoveryOwner(models.TextChoices):
        CREATOR = "creator", "Creator"
        AGENCY = "agency", "Agency"
        SHARED = "shared", "Shared"

    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="channels",
    )
    platform = models.CharField(max_length=20, choices=Platform.choices)
    handle = models.CharField(max_length=160)
    status = models.CharField(max_length=20, choices=Status.choices)
    access_mode = models.CharField(max_length=40, choices=AccessMode.choices)
    recovery_owner = models.CharField(max_length=20, choices=RecoveryOwner.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("platform", "handle"),
                name="uniq_platform_handle_exact",
            )
        ]

    def clean(self):
        validate_platform_handle_unique_ci(self)

    def __str__(self) -> str:
        return f"{self.creator.display_name} / {self.platform} / {self.handle}"


class OperatorAssignment(models.Model):
    class Scope(models.TextChoices):
        FULL_MANAGEMENT = "full_management", "Full management"
        POSTING_ONLY = "posting_only", "Posting only"
        DRAFT_ONLY = "draft_only", "Draft only"
        ANALYTICS_ONLY = "analytics_only", "Analytics only"

    operator = models.ForeignKey(
        Operator,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    scope = models.CharField(max_length=30, choices=Scope.choices)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def clean(self):
        validate_no_overlapping_assignments(self)

    def __str__(self) -> str:
        return f"{self.operator} -> {self.creator} ({self.scope})"
