from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView

from core.forms import ChannelHandoffForm
from core.models import CreatorChannel
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

    def _get_assignments_for_creator(self, creator):
        if is_admin_user(self.request.user):
            return list(
                get_active_assignments_queryset()
                .select_related("operator", "operator__user", "creator")
                .filter(creator=creator)
            )

        operator = get_operator_for_user(self.request.user)
        if operator is None:
            return []

        return list(
            get_active_assignments_for_operator(operator)
            .select_related("operator", "operator__user", "creator")
            .filter(creator=creator)
        )

    def _build_risk_flags(self, channel, creator, policy_gap, handoff_missing):
        risk_flags = []

        if creator.status != "active":
            risk_flags.append(
                {
                    "key": "creator_status",
                    "label": f"Creator status not active ({creator.get_status_display()})",
                }
            )

        if creator.consent_status != "active":
            risk_flags.append(
                {
                    "key": "consent",
                    "label": f"Consent not active ({creator.get_consent_status_display()})",
                }
            )

        if channel.status != "active":
            risk_flags.append(
                {
                    "key": "channel_status",
                    "label": f"Channel status not active ({channel.get_status_display()})",
                }
            )

        if (
            channel.credential_status
            and channel.credential_status != CreatorChannel.CredentialStatus.KNOWN
        ):
            risk_flags.append(
                {
                    "key": "credential_issues",
                    "label": f"Credential issue ({channel.get_credential_status_display()})",
                }
            )

        if not channel.two_factor_enabled:
            risk_flags.append(
                {
                    "key": "no_2fa",
                    "label": "No 2FA enabled",
                }
            )

        if policy_gap:
            risk_flags.append(
                {
                    "key": "policy_gap",
                    "label": "Policy gap",
                }
            )

        if not creator.primary_link:
            risk_flags.append(
                {
                    "key": "missing_primary_link",
                    "label": "Missing primary link",
                }
            )

        if handoff_missing:
            risk_flags.append(
                {
                    "key": "missing_handoff",
                    "label": "Missing structured session handoff",
                }
            )

        return risk_flags

    def _build_quick_action_groups(self, channel, creator):
        start_actions = []
        if channel.profile_url:
            start_actions.append(
                {
                    "kind": "link",
                    "label": "Open Instagram profiel",
                    "url": channel.profile_url,
                    "external": True,
                }
            )
        if creator.primary_link:
            start_actions.append(
                {
                    "kind": "link",
                    "label": "Open primary link",
                    "url": creator.primary_link,
                    "external": True,
                }
            )
        if creator.content_source_url:
            start_actions.append(
                {
                    "kind": "link",
                    "label": "Open source URL",
                    "url": creator.content_source_url,
                    "external": True,
                }
            )
        start_actions.append(
            {
                "kind": "link",
                "label": "Open creator detail",
                "url": reverse("creator-detail", kwargs={"pk": creator.pk}),
                "external": False,
            }
        )

        execute_actions = []
        if creator.primary_link:
            execute_actions.append(
                {
                    "kind": "copy",
                    "label": "Kopieer primary link",
                    "copy_value": creator.primary_link,
                }
            )
        if channel.login_identifier:
            execute_actions.append(
                {
                    "kind": "value_copy",
                    "label": "Login identifier",
                    "value": channel.login_identifier,
                    "copy_label": "Kopieer login identifier",
                }
            )

        close_actions = [
            {
                "kind": "jump",
                "label": "Ga naar sessie-afsluiting",
                "url": "#session-closeout",
            }
        ]

        groups = []
        if start_actions:
            groups.append({"title": "Starten", "actions": start_actions})
        if execute_actions:
            groups.append({"title": "Uitvoeren", "actions": execute_actions})
        if close_actions:
            groups.append({"title": "Afsluiten", "actions": close_actions})
        return groups

    def _build_latest_session_context(self, channel):
        return {
            "available": channel.has_structured_session_handoff(),
            "what_done": channel.session_what_done,
            "next_action": channel.session_next_action,
            "blockers": channel.session_blockers,
            "policy_context_reviewed": channel.session_policy_context_reviewed,
            "updated_at": channel.session_updated_at,
            "legacy_summary": channel.last_operator_update,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel = self.object
        creator = channel.creator

        assignments = self._get_assignments_for_creator(creator)
        materials = list(
            creator.materials.filter(active=True).select_related("uploaded_by")
        )

        policy_gap = channel.vpn_required and not (
            channel.approved_ip_label or channel.approved_egress_ip
        )
        handoff_missing = not channel.has_structured_session_handoff()

        risk_flags = self._build_risk_flags(
            channel=channel,
            creator=creator,
            policy_gap=policy_gap,
            handoff_missing=handoff_missing,
        )

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

        handoff_form = kwargs.get("handoff_form")
        if handoff_form is None:
            handoff_form = ChannelHandoffForm(channel=channel)

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
                "quick_action_groups": self._build_quick_action_groups(channel, creator),
                "latest_session": self._build_latest_session_context(channel),
                "back_url": reverse("channel-detail", kwargs={"pk": channel.pk}),
                "handoff_form": handoff_form,
                "saved": self.request.GET.get("saved") == "1",
                "review_required_warning": policy_state["label"] == "review required",
                "blocked_warning": policy_state["label"] == "blocked",
                "can_edit_channel": is_admin_user(self.request.user),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        handoff_form = ChannelHandoffForm(request.POST, channel=self.object)

        if not handoff_form.is_valid():
            return self.render_to_response(
                self.get_context_data(handoff_form=handoff_form)
            )

        update_fields = self.object.apply_workspace_session(
            what_done=handoff_form.cleaned_data["session_what_done"],
            next_action=handoff_form.cleaned_data["session_next_action"],
            blockers=handoff_form.cleaned_data["session_blockers"],
            policy_context_reviewed=handoff_form.cleaned_data[
                "session_policy_context_reviewed"
            ],
            updated_at=timezone.now(),
        )
        self.object.save(update_fields=update_fields)

        redirect_url = reverse("instagram-workspace", kwargs={"pk": self.object.pk})
        redirect_url = f"{redirect_url}?saved=1"
        return HttpResponseRedirect(redirect_url)