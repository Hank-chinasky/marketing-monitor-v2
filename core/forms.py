from datetime import datetime, time

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from core.models import Creator, CreatorChannel, Operator, OperatorAssignment

UserModel = get_user_model()


class OperatorCreateForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")
    email = forms.EmailField(required=False, label="E-mail")
    first_name = forms.CharField(max_length=150, required=False, label="Voornaam")
    last_name = forms.CharField(max_length=150, required=False, label="Achternaam")
    password1 = forms.CharField(
        label="Wachtwoord",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Herhaal wachtwoord",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if UserModel.objects.filter(username=username).exists():
            raise forms.ValidationError("Deze username bestaat al.")
        return username

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "De wachtwoorden komen niet overeen.")

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
                "Een actieve creator vereist consent_status='active'.",
            )

        return cleaned


class CreatorChannelForm(forms.ModelForm):
    last_access_check_at = forms.DateField(
        label="Laatste access check",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    last_ip_check_at = forms.DateField(
        label="Laatste IP check",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    last_operator_update_at = forms.DateField(
        label="Laatste operator update datum",
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
            "last_operator_update",
            "last_operator_update_at",
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

        if instance.last_operator_update_at:
            self.initial["last_operator_update_at"] = timezone.localtime(
                instance.last_operator_update_at
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

    def clean_last_operator_update_at(self):
        return self._date_to_aware_datetime(self.cleaned_data.get("last_operator_update_at"))


class OperatorAssignmentForm(forms.ModelForm):
    starts_at = forms.DateField(
        label="Startdatum",
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    ends_at = forms.DateField(
        label="Einddatum",
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