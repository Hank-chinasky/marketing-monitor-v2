import mimetypes
import os

from django.conf import settings
from django.core.exceptions import ValidationError
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

    class ContentSourceType(models.TextChoices):
        SHARED_DRIVE = "shared_drive", "Shared drive"
        DROPBOX = "dropbox", "Dropbox"
        ONEDRIVE = "onedrive", "OneDrive"
        TELEGRAM = "telegram", "Telegram"
        EMAIL = "email", "Email"
        INTERNAL_STORAGE = "internal_storage", "Internal storage"
        MIXED = "mixed", "Mixed"
        OTHER = "other", "Other"

    class ContentReadyStatus(models.TextChoices):
        WAITING_FOR_CREATOR = "waiting_for_creator", "Waiting for creator"
        UPLOADED = "uploaded", "Uploaded"
        READY_TO_POST = "ready_to_post", "Ready to post"
        POSTED = "posted", "Posted"
        BLOCKED = "blocked", "Blocked"

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
    primary_link = models.URLField(blank=True)

    content_source_type = models.CharField(
        max_length=30,
        choices=ContentSourceType.choices,
        blank=True,
    )
    content_source_url = models.URLField(blank=True)
    content_source_notes = models.TextField(blank=True)
    content_ready_status = models.CharField(
        max_length=30,
        choices=ContentReadyStatus.choices,
        blank=True,
    )

    def clean(self):
        validate_active_creator_requires_active_consent(self)

    def __str__(self) -> str:
        return self.display_name


class CreatorMaterial(models.Model):
    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="materials",
    )
    file = models.FileField(upload_to="creator_materials/%Y/%m/%d")
    label = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_creator_materials",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self) -> str:
        return self.label or self.filename

    @property
    def filename(self) -> str:
        return os.path.basename(self.file.name)

    @property
    def extension(self) -> str:
        _, ext = os.path.splitext(self.file.name or "")
        return ext.lower().lstrip(".")

    @property
    def mime_type(self) -> str:
        guessed, _ = mimetypes.guess_type(self.file.name or "")
        return guessed or "application/octet-stream"

    @property
    def media_kind(self) -> str:
        mime_type = self.mime_type
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("video/"):
            return "video"
        return "other"

    @property
    def is_image(self) -> bool:
        return self.media_kind == "image"

    @property
    def is_video(self) -> bool:
        return self.media_kind == "video"

    @property
    def is_previewable(self) -> bool:
        return self.media_kind in {"image", "video"}


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

    class CredentialStatus(models.TextChoices):
        KNOWN = "known", "Known"
        HELD_BY_CREATOR = "held_by_creator", "Held by creator"
        STORED_ELSEWHERE = "stored_elsewhere", "Stored elsewhere"
        NEEDS_RESET = "needs_reset", "Needs reset"

    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="channels",
    )
    platform = models.CharField(max_length=20, choices=Platform.choices)
    handle = models.CharField(max_length=160)
    profile_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    access_mode = models.CharField(max_length=40, choices=AccessMode.choices)
    recovery_owner = models.CharField(max_length=20, choices=RecoveryOwner.choices)

    login_identifier = models.CharField(max_length=255, blank=True)
    account_email = models.EmailField(blank=True)
    account_phone_number = models.CharField(max_length=64, blank=True)

    credential_status = models.CharField(
        max_length=30,
        choices=CredentialStatus.choices,
        blank=True,
    )
    access_notes = models.TextField(blank=True)
    last_access_check_at = models.DateTimeField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)

    vpn_required = models.BooleanField(default=False)
    approved_egress_ip = models.CharField(max_length=64, blank=True)
    approved_ip_label = models.CharField(max_length=120, blank=True)
    approved_access_region = models.CharField(max_length=64, blank=True)
    access_profile_notes = models.TextField(blank=True)
    last_ip_check_at = models.DateTimeField(null=True, blank=True)

    last_operator_update = models.TextField(blank=True)
    last_operator_update_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("platform", "handle"),
                name="uniq_platform_handle_exact",
            )
        ]

    def clean(self):
        validate_platform_handle_unique_ci(self)

        if self.vpn_required and not (
            (self.approved_ip_label or "").strip() or (self.approved_egress_ip or "").strip()
        ):
            raise ValidationError(
                {
                    "approved_ip_label": "Set an approved IP label or approved egress IP when VPN is required.",
                    "approved_egress_ip": "Set an approved IP label or approved egress IP when VPN is required.",
                }
            )

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


class ProfileOpportunity(models.Model):
    class ScoreValue(models.IntegerChoices):
        ZERO = 0, "0"
        ONE = 1, "1"
        TWO = 2, "2"

    class RiskPenaltyValue(models.IntegerChoices):
        ZERO = 0, "0"
        NEGATIVE_ONE = -1, "-1"
        NEGATIVE_TWO = -2, "-2"

    class PriorityBand(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class ActionBucket(models.TextChoices):
        NOW = "nu_oppakken", "Nu oppakken"
        LATER = "later", "Later"
        NOT_WORTH = "niet_waard", "Niet waard"

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_profile_opportunities",
    )
    intake_name = models.CharField(max_length=255)
    profile_url = models.URLField(blank=True)
    intake_notes = models.TextField(blank=True)
    handoff_note = models.TextField(blank=True)

    source_quality_score = models.PositiveSmallIntegerField(
        choices=ScoreValue.choices,
        default=ScoreValue.ZERO,
    )
    profile_signal_score = models.PositiveSmallIntegerField(
        choices=ScoreValue.choices,
        default=ScoreValue.ZERO,
    )
    intent_guess_score = models.PositiveSmallIntegerField(
        choices=ScoreValue.choices,
        default=ScoreValue.ZERO,
    )
    target_fit_score = models.PositiveSmallIntegerField(
        choices=ScoreValue.choices,
        default=ScoreValue.ZERO,
    )
    risk_penalty_score = models.SmallIntegerField(
        choices=RiskPenaltyValue.choices,
        default=RiskPenaltyValue.ZERO,
    )

    total_score = models.SmallIntegerField(default=0, editable=False)
    priority_band = models.CharField(
        max_length=16,
        choices=PriorityBand.choices,
        default=PriorityBand.LOW,
        editable=False,
    )
    action_bucket = models.CharField(
        max_length=24,
        choices=ActionBucket.choices,
        default=ActionBucket.NOT_WORTH,
        editable=False,
    )
    score_reason_short = models.CharField(max_length=255, blank=True, editable=False)

    manual_override = models.BooleanField(default=False)
    override_priority_band = models.CharField(
        max_length=16,
        choices=PriorityBand.choices,
        blank=True,
    )
    override_action_bucket = models.CharField(
        max_length=24,
        choices=ActionBucket.choices,
        blank=True,
    )
    override_reason_short = models.CharField(max_length=140, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def clean(self):
        errors = {}

        if self.manual_override:
            if not (self.override_priority_band or "").strip():
                errors["override_priority_band"] = "Kies een override priority band."
            if not (self.override_action_bucket or "").strip():
                errors["override_action_bucket"] = "Kies een override action bucket."
            if not (self.override_reason_short or "").strip():
                errors["override_reason_short"] = "Geef een korte override reden."

        if errors:
            raise ValidationError(errors)

    def apply_scoring(self):
        from core.services.opportunity_scoring import evaluate_opportunity

        result = evaluate_opportunity(
            source_quality_score=self.source_quality_score,
            profile_signal_score=self.profile_signal_score,
            intent_guess_score=self.intent_guess_score,
            target_fit_score=self.target_fit_score,
            risk_penalty_score=self.risk_penalty_score,
        )
        self.total_score = result.total_score
        self.priority_band = result.priority_band
        self.action_bucket = result.action_bucket
        self.score_reason_short = result.score_reason_short

    @property
    def effective_priority_band(self) -> str:
        if self.manual_override and self.override_priority_band:
            return self.override_priority_band
        return self.priority_band

    @property
    def effective_action_bucket(self) -> str:
        if self.manual_override and self.override_action_bucket:
            return self.override_action_bucket
        return self.action_bucket

    def save(self, *args, **kwargs):
        if not self.manual_override:
            self.override_priority_band = ""
            self.override_action_bucket = ""
            self.override_reason_short = ""

        self.apply_scoring()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.intake_name


class OutcomeEntry(models.Model):
    class OutcomeType(models.TextChoices):
        GEEN_REACTIE = "geen_reactie", "Geen reactie"
        GESPREK_GESTART = "gesprek_gestart", "Gesprek gestart"
        WARM_VERVOLG = "warm_vervolg", "Warm vervolg"
        CONVERSION = "conversion", "Conversion"
        AFGEVALLEN = "afgevallen", "Afgevallen"
        ONDUIDELIJK = "onduidelijk", "Onduidelijk"

    opportunity = models.ForeignKey(
        "core.ProfileOpportunity",
        on_delete=models.CASCADE,
        related_name="outcomes",
    )
    outcome_type = models.CharField(max_length=32, choices=OutcomeType.choices)
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profile_opportunity_outcomes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.opportunity.intake_name} / {self.get_outcome_type_display()}"
