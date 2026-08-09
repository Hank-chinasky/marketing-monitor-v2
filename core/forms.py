from datetime import datetime, time

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from core.models import (
    ConversationThread,
    Creator,
    CreatorChannel,
    Operator,
    OperatorAssignment,
)
from core.services.scope import (
    get_channel_queryset_for_user,
    get_creator_queryset_for_user,
)

UserModel = get_user_model()


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]

        if data:
            return [single_file_clean(data, initial)]

        return []


class OperatorCreateForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")
    email = forms.EmailField(required=False, label="E-mail")
    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Repeat password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if UserModel.objects.filter(username=username).exists():
            raise forms.ValidationError("This username already exists.")
        return username

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")

        return cleaned

    @transaction.atomic
    def save(self):
        username = self.cleaned_data["username"]
        email = (self.cleaned_data.get("email") or "").strip()
        first_name = (self.cleaned_data.get("first_name") or "").strip()
        last_name = (self.cleaned_data.get("last_name") or "").strip()
        password = self.cleaned_data["password1"]

        user = UserModel.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        operator = Operator.objects.create(user=user)
        return operator


class OperatorUpdateForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")
    email = forms.EmailField(required=False, label="E-mail")
    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")
    is_active = forms.BooleanField(
        required=False,
        label="Account active",
        help_text="Disable this to block the operator from signing in.",
    )

    def __init__(self, *args, operator, **kwargs):
        self.operator = operator
        super().__init__(*args, **kwargs)

        user = self.operator.user
        self.fields["username"].initial = user.username
        self.fields["email"].initial = user.email
        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["is_active"].initial = user.is_active

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        qs = UserModel.objects.filter(username=username).exclude(pk=self.operator.user.pk)
        if qs.exists():
            raise forms.ValidationError("This username already exists.")
        return username

    @transaction.atomic
    def save(self):
        user = self.operator.user
        user.username = self.cleaned_data["username"]
        user.email = (self.cleaned_data.get("email") or "").strip()
        user.first_name = (self.cleaned_data.get("first_name") or "").strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()
        user.is_active = bool(self.cleaned_data.get("is_active"))
        user.save()
        return self.operator


class OperatorPasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Repeat new password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, operator, **kwargs):
        self.operator = operator
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")

        return cleaned

    @transaction.atomic
    def save(self):
        user = self.operator.user
        user.set_password(self.cleaned_data["password1"])
        user.save()
        return self.operator


class CreatorForm(forms.ModelForm):
    class Meta:
        model = Creator
        fields = [
            "display_name",
            "legal_name",
            "status",
            "consent_status",
            "primary_operator",
            "notes",
            "primary_link",
            "content_source_type",
            "content_source_url",
            "content_source_notes",
            "content_ready_status",
        ]

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        consent_status = cleaned.get("consent_status")

        if status == "active" and consent_status != "active":
            self.add_error(
                "consent_status",
                "An active creator requires consent_status='active'.",
            )

        return cleaned


class CreatorMaterialUploadForm(forms.Form):
    file = MultipleFileField(
        label="Files",
        help_text="You can select multiple files at once.",
    )
    label = forms.CharField(
        max_length=255,
        required=False,
        label="Label",
        help_text="For multiple files, this is used as a prefix.",
    )
    notes = forms.CharField(
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_file(self):
        files = self.cleaned_data.get("file") or []
        if not files:
            raise forms.ValidationError("Select at least one file.")
        return files


class ChannelHandoffForm(forms.Form):
    session_what_done = forms.CharField(
        label="Work completed",
        required=True,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Briefly describe what was completed in this session.",
            }
        ),
        help_text="Required. Keep it concrete and operational.",
    )
    session_next_action = forms.CharField(
        label="Next action",
        required=True,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "maxlength": 255,
                "placeholder": "Describe the next concrete step.",
            }
        ),
        help_text="Required. One clear next step.",
    )
    session_blockers = forms.CharField(
        label="Blockers / open issues",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Optional: record blockers or open issues.",
            }
        ),
        help_text="Optional. Leave blank when there are no blockers.",
    )
    session_policy_context_reviewed = forms.BooleanField(
        label="Policy/disclosure context reviewed",
        required=True,
        help_text="Required. Confirm that you reviewed the policy and disclosure context before closing.",
    )

    def __init__(self, *args, channel=None, **kwargs):
        super().__init__(*args, **kwargs)

        if channel is not None and not self.is_bound:
            self.initial.setdefault("session_what_done", channel.session_what_done)
            self.initial.setdefault("session_next_action", channel.session_next_action)
            self.initial.setdefault("session_blockers", channel.session_blockers)
            self.initial.setdefault(
                "session_policy_context_reviewed",
                channel.session_policy_context_reviewed,
            )

    def clean_session_what_done(self):
        return (self.cleaned_data.get("session_what_done") or "").strip()

    def clean_session_next_action(self):
        return (self.cleaned_data.get("session_next_action") or "").strip()

    def clean_session_blockers(self):
        return (self.cleaned_data.get("session_blockers") or "").strip()


class CreatorChannelForm(forms.ModelForm):
    last_access_check_at = forms.DateField(
        label="Latest access check",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    last_ip_check_at = forms.DateField(
        label="Latest IP check",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )

    class Meta:
        model = CreatorChannel
        fields = [
            "creator",
            "platform",
            "handle",
            "profile_url",
            "status",
            "access_mode",
            "recovery_owner",
            "login_identifier",
            "account_email",
            "account_phone_number",
            "credential_status",
            "access_notes",
            "last_access_check_at",
            "two_factor_enabled",
            "vpn_required",
            "approved_egress_ip",
            "approved_ip_label",
            "approved_access_region",
            "access_profile_notes",
            "last_ip_check_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = getattr(self, "instance", None)
        if not instance or not instance.pk:
            return

        if instance.last_access_check_at:
            self.initial["last_access_check_at"] = timezone.localtime(
                instance.last_access_check_at
            ).date()

        if instance.last_ip_check_at:
            self.initial["last_ip_check_at"] = timezone.localtime(
                instance.last_ip_check_at
            ).date()

    def _date_to_aware_datetime(self, value):
        if not value:
            return None
        dt = datetime.combine(value, time.min)
        return timezone.make_aware(dt, timezone.get_current_timezone())

    def clean_last_access_check_at(self):
        return self._date_to_aware_datetime(self.cleaned_data.get("last_access_check_at"))

    def clean_last_ip_check_at(self):
        return self._date_to_aware_datetime(self.cleaned_data.get("last_ip_check_at"))


class ConversationThreadForm(forms.ModelForm):
    class Meta:
        model = ConversationThread
        fields = [
            "creator",
            "channel",
            "source_system",
            "source_thread_id",
            "status",
            "last_message_at",
            "thread_summary",
            "open_loop",
            "guardrails",
            "risk_flags",
            "last_handoff_note",
            "last_approved_reply_style",
            "active",
        ]
        widgets = {
            "last_message_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "thread_summary": forms.Textarea(attrs={"rows": 4}),
            "open_loop": forms.Textarea(attrs={"rows": 3}),
            "guardrails": forms.Textarea(attrs={"rows": 4}),
            "risk_flags": forms.Textarea(attrs={"rows": 3}),
            "last_handoff_note": forms.Textarea(attrs={"rows": 4}),
            "last_approved_reply_style": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.scoped_creator_queryset = get_creator_queryset_for_user(user)
        self.scoped_channel_queryset = get_channel_queryset_for_user(user)

        self.fields["creator"].queryset = self.scoped_creator_queryset.order_by(
            "display_name"
        )
        self.fields["channel"].queryset = self.scoped_channel_queryset.order_by(
            "creator__display_name",
            "platform",
            "handle",
        )
        self.fields["channel"].required = False

        if not self.is_bound and not self.instance.pk:
            self.initial.setdefault(
                "source_system",
                ConversationThread.SourceSystem.MARA_CHAT,
            )
            self.initial.setdefault("active", True)

    def clean_source_thread_id(self):
        return (self.cleaned_data.get("source_thread_id") or "").strip()

    def clean(self):
        cleaned = super().clean()
        creator = cleaned.get("creator")
        channel = cleaned.get("channel")

        if creator and not self.scoped_creator_queryset.filter(pk=creator.pk).exists():
            self.add_error("creator", "Creator is outside your scope.")

        if channel and not self.scoped_channel_queryset.filter(pk=channel.pk).exists():
            self.add_error("channel", "Channel is outside your scope.")

        if creator and channel and channel.creator_id != creator.pk:
            self.add_error("channel", "Channel does not belong to the selected creator.")

        return cleaned


class OperatorAssignmentForm(forms.ModelForm):
    starts_at = forms.DateField(
        label="Start date",
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    ends_at = forms.DateField(
        label="End date",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )

    class Meta:
        model = OperatorAssignment
        fields = [
            "operator",
            "creator",
            "scope",
            "starts_at",
            "ends_at",
            "active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = getattr(self, "instance", None)
        if not instance or not instance.pk:
            return

        if instance.starts_at:
            self.initial["starts_at"] = timezone.localtime(instance.starts_at).date()
        if instance.ends_at:
            self.initial["ends_at"] = timezone.localtime(instance.ends_at).date()

    def clean_starts_at(self):
        start_date = self.cleaned_data["starts_at"]
        start_dt = datetime.combine(start_date, time.min)
        return timezone.make_aware(start_dt, timezone.get_current_timezone())

    def clean_ends_at(self):
        end_date = self.cleaned_data.get("ends_at")
        if not end_date:
            return None

        end_dt = datetime.combine(end_date, time.min)
        return timezone.make_aware(end_dt, timezone.get_current_timezone())
