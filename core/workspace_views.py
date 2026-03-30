from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import DetailView

from core.forms import ChannelOperationalStateForm
from core.models import CreatorChannel
from core.services.operational_state import get_or_create_channel_operational_state
from core.services.scope import (
    get_active_assignments_for_operator,
    get_active_assignments_queryset,
    get_instagram_workspace_channel_queryset_for_user,
    get_operator_for_user,
    is_admin_user,
)


class InstagramWorkspaceView(LoginRequiredMixin, DetailView):
    model = CreatorChannel
    template_name = "workspaces/instagram_workspace.html"
    context_object_name = "channel"

    def get_queryset(self):
        return (
            get_instagram_workspace_channel_queryset_for_user(self.request.user)
            .select_related(
                "creator",
                "creator__primary_operator",
                "creator__primary_operator__user",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel = self.object
        creator = channel.creator
        operational_state = get_or_create_channel_operational_state(channel)
        operational_state_form = ChannelOperationalStateForm(instance=operational_state)

        if is_admin_user(self.request.user):
            assignments = list(
                get_active_assignments_queryset()
                .select_related("operator", "operator__user", "creator")
                .filter(creator=creator)
            )
        else:
            operator = get_operator_for_user(self.request.user)
            assignments = list(
                get_active_assignments_for_operator(operator)
                .select_related("operator", "operator__user", "creator")
                .filter(creator=creator)
            ) if operator else []

        materials = list(
            creator.materials.filter(active=True).select_related("uploaded_by")
        )
        policy_gap = channel.vpn_required and not (
            channel.approved_ip_label or channel.approved_egress_ip
        )
        handoff_missing = not bool((operational_state.last_update or "").strip())

        risk_flags = []
        if creator.status != "active":
            risk_flags.append("creator_status")
        if creator.consent_status != "active":
            risk_flags.append("consent")
        if channel.status != "active":
            risk_flags.append("channel_status")
        if channel.credential_status == "needs_reset":
            risk_flags.append("credentials")
        if not channel.two_factor_enabled:
            risk_flags.append("no_2fa")
        if policy_gap:
            risk_flags.append("policy_gap")
        if not creator.primary_link:
            risk_flags.append("missing_primary_link")
        if handoff_missing:
            risk_flags.append("missing_handoff")

        human_review_required = bool(risk_flags)

        if (
            creator.status != "active"
            or creator.consent_status != "active"
            or channel.status != "active"
        ):
            policy_state = {"label": "blocked", "badge": "badge-red"}
        elif human_review_required:
            policy_state = {"label": "review required", "badge": "badge-yellow"}
        else:
            policy_state = {"label": "ready", "badge": "badge-green"}

        quick_actions = []
        if channel.profile_url:
            quick_actions.append(
                {
                    "label": "Open Instagram profiel",
                    "url": channel.profile_url,
                    "external": True,
                }
            )
        if creator.primary_link:
            quick_actions.append(
                {
                    "label": "Open primary link",
                    "url": creator.primary_link,
                    "external": True,
                }
            )
        quick_actions.append(
            {
                "label": "Open creator detail",
                "url": reverse("creator-detail", kwargs={"pk": creator.pk}),
                "external": False,
            }
        )

        context.update(
            {
                "creator": creator,
                "assignments": assignments,
                "materials": materials,
                "policy_gap": policy_gap,
                "handoff_missing": handoff_missing,
                "risk_flags": risk_flags,
                "human_review_required": human_review_required,
                "policy_state": policy_state,
                "quick_actions": quick_actions,
                "back_url": reverse("channel-detail", kwargs={"pk": channel.pk}),
                "operational_state": operational_state,
                "operational_state_form": operational_state_form,
            }
        )
        return context