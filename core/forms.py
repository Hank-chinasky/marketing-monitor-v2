from django import forms

from core.models import Creator, CreatorChannel, OperatorAssignment


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
            "status",
            "access_mode",
            "recovery_owner",
        ]


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
