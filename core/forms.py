from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

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
        widgets = {
            "last_access_check_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "last_ip_check_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "last_operator_update_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class OperatorAssignmentForm(forms.ModelForm):
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
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }