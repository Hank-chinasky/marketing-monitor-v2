import mimetypes
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

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

    session_what_done = models.TextField(blank=True, default="")
    session_next_action = models.CharField(max_length=255, blank=True, default="")
    session_blockers = models.TextField(blank=True, default="")
    session_policy_context_reviewed = models.BooleanField(default=False)
    session_updated_at = models.DateTimeField(null=True, blank=True)

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
            (self.approved_ip_label or "").strip()
            or (self.approved_egress_ip or "").strip()
        ):
            raise ValidationError(
                {
                    "approved_ip_label": "Set an approved IP label or approved egress IP when VPN is required.",
                    "approved_egress_ip": "Set an approved IP label or approved egress IP when VPN is required.",
                }
            )

    def has_structured_session_handoff(self) -> bool:
        return bool(
            (self.session_what_done or "").strip()
            and (self.session_next_action or "").strip()
            and self.session_policy_context_reviewed
            and self.session_updated_at is not None
        )

    def build_workspace_session_summary(self) -> str:
        what_done = (self.session_what_done or "").strip()
        next_action = (self.session_next_action or "").strip()
        blockers = (self.session_blockers or "").strip() or "-"
        reviewed = "Ja" if self.session_policy_context_reviewed else "Nee"

        return "\n\n".join(
            [
                f"Wat gedaan:\n{what_done}",
                f"Next action:\n{next_action}",
                f"Blockers / open issues:\n{blockers}",
                f"Policy/disclosure context reviewed: {reviewed}",
            ]
        )

    def apply_workspace_session(
        self,
        *,
        what_done: str,
        next_action: str,
        blockers: str = "",
        policy_context_reviewed: bool,
        updated_at=None,
    ):
        timestamp = updated_at or timezone.now()

        self.session_what_done = (what_done or "").strip()
        self.session_next_action = (next_action or "").strip()
        self.session_blockers = (blockers or "").strip()
        self.session_policy_context_reviewed = bool(policy_context_reviewed)
        self.session_updated_at = timestamp

        self.last_operator_update = self.build_workspace_session_summary()
        self.last_operator_update_at = timestamp if self.last_operator_update else None

        return [
            "session_what_done",
            "session_next_action",
            "session_blockers",
            "session_policy_context_reviewed",
            "session_updated_at",
            "last_operator_update",
            "last_operator_update_at",
        ]

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


class ConversationThread(models.Model):
    class SourceSystem(models.TextChoices):
        MARA_CHAT = "mara_chat", "Mara chat"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        WAITING_ON_OPERATOR = "waiting_on_operator", "Waiting on operator"
        WAITING_ON_CUSTOMER = "waiting_on_customer", "Waiting on customer"
        HANDOFF_REQUIRED = "handoff_required", "Handoff required"
        CLOSED = "closed", "Closed"

    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="conversation_threads",
    )
    channel = models.ForeignKey(
        CreatorChannel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversation_threads",
    )
    source_system = models.CharField(
        max_length=32,
        choices=SourceSystem.choices,
        default=SourceSystem.MARA_CHAT,
    )
    source_thread_id = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_operator_handoff_at = models.DateTimeField(null=True, blank=True)
    thread_summary = models.TextField(blank=True)
    open_loop = models.TextField(blank=True)
    guardrails = models.TextField(blank=True)
    risk_flags = models.TextField(blank=True)
    last_handoff_note = models.TextField(blank=True)
    last_approved_reply_style = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_system", "source_thread_id"),
                name="uniq_convthread_source_thread",
            )
        ]
        indexes = [
            models.Index(fields=("status",), name="convthread_status_idx"),
            models.Index(fields=("last_message_at",), name="convthread_last_msg_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.creator.display_name} / {self.source_system} / {self.source_thread_id}"


class Approval(models.Model):
    class Type(models.TextChoices):
        CONTENT_APPROVAL = "content_approval", "Content approval"
        ACTION_APPROVAL = "action_approval", "Action approval"
        ACCESS_EXCEPTION = "access_exception", "Access exception"

    class Status(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not required"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="approvals",
    )
    thread = models.ForeignKey(
        ConversationThread,
        on_delete=models.CASCADE,
        related_name="approvals",
        null=True,
        blank=True,
    )
    approval_type = models.CharField(max_length=32, choices=Type.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    summary = models.CharField(max_length=255, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_approvals",
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decided_approvals",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=("creator", "status"), name="approval_creator_status_idx"),
            models.Index(fields=("thread", "status"), name="approval_thread_status_idx"),
        ]

    def clean(self):
        super().clean()
        if self.thread_id and self.creator_id and self.thread.creator_id != self.creator_id:
            raise ValidationError(
                {
                    "thread": "Approval thread must belong to the same creator as the approval.",
                    "creator": "Approval creator must match the thread creator.",
                }
            )

    def save(self, *args, **kwargs):
       # self.full_clean()
        super().save(*args, **kwargs)

    def approve(self, user):
        if self.status != self.Status.PENDING:
            raise ValidationError("Approval can only be approved from pending.")

        self.status = self.Status.APPROVED
        self.decided_by = user
        self.decided_at = timezone.now()
        self.save(update_fields=["status", "decided_by", "decided_at"])

    def reject(self, user):
        if self.status != self.Status.PENDING:
            raise ValidationError("Approval can only be rejected from pending.")

        self.status = self.Status.REJECTED
        self.decided_by = user
        self.decided_at = timezone.now()
        self.save(update_fields=["status", "decided_by", "decided_at"])

    def __str__(self) -> str:
        target = self.thread.source_thread_id if self.thread else self.creator.display_name
        return f"{self.get_approval_type_display()} / {self.get_status_display()} / {target}"


class BuddyDraft(models.Model):
    class State(models.TextChoices):
        DRAFTED = "drafted", "Drafted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class GenerationSource(models.TextChoices):
        STUB = "stub", "Stub"
        BUDDY_API = "buddy_api", "Buddy API"

    thread = models.ForeignKey(
        ConversationThread,
        on_delete=models.CASCADE,
        related_name="buddy_drafts",
    )
    reply_text = models.TextField()
    intent = models.CharField(max_length=100)
    tone = models.CharField(max_length=100)
    confidence = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        null=True,
        blank=True,
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
    )
    requires_human_attention = models.BooleanField(default=True)
    handoff_note = models.TextField(blank=True)
    state = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.DRAFTED,
    )
    generation_source = models.CharField(
        max_length=20,
        choices=GenerationSource.choices,
        default=GenerationSource.STUB,
    )
    created_for_operator = models.ForeignKey(
        Operator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buddy_drafts_created_for",
    )
    approved_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_buddy_drafts",
    )
    edited_after_generation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    def is_drafted(self) -> bool:
        return self.state == self.State.DRAFTED

    def is_approved(self) -> bool:
        return self.state == self.State.APPROVED

    def is_rejected(self) -> bool:
        return self.state == self.State.REJECTED

    def __str__(self) -> str:
        return f"{self.thread} / {self.state}"
