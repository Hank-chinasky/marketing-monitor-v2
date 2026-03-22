from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from core.authz import scope_assignments_queryset, scope_channels_queryset
from core.forms import CreatorChannelForm, CreatorForm, OperatorAssignmentForm
from core.mixins import (
    AdminOnlyMixin,
    ScopedAssignmentQuerysetMixin,
    ScopedChannelQuerysetMixin,
    ScopedCreatorObjectMixin,
    ScopedCreatorQuerysetMixin,
)
from core.models import Creator, CreatorChannel, Operator, OperatorAssignment


def append_query_parameter(url, key, value):
    parts = urlsplit(url)
    query_items = dict(parse_qsl(parts.query, keep_blank_values=True))
    query_items[key] = value
    new_query = urlencode(query_items)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def get_safe_next_url(request):
    next_url = (request.POST.get("next") or request.GET.get("next") or "").strip()

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return ""


class OperationsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/operations_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        creators = list(
            CreatorListView.request_scoped_queryset(self.request).select_related(
                "primary_operator"
            )
        )
        channels = list(
            scope_channels_queryset(
                self.request.user,
                qs=CreatorChannel.objects.select_related("creator"),
            )
        )
        assignments = list(
            scope_assignments_queryset(
                self.request.user,
                qs=OperatorAssignment.objects.select_related(
                    "creator",
                    "operator",
                    "operator__user",
                ),
            )
        )

        channels_needing_reset = [
            channel for channel in channels if channel.credential_status == "needs_reset"
        ]
        channels_without_2fa = [
            channel for channel in channels if not channel.two_factor_enabled
        ]
        vpn_policy_gaps = [
            channel
            for channel in channels
            if channel.vpn_required
            and not (channel.approved_ip_label or channel.approved_egress_ip)
        ]
        consent_issues = [
            creator for creator in creators if creator.consent_status != "active"
        ]
        paused_or_offboarded = [
            creator for creator in creators if creator.status != "active"
        ]

        assigned_creator_ids = {assignment.creator_id for assignment in assignments}
        creators_without_active_assignment = [
            creator for creator in creators if creator.pk not in assigned_creator_ids
        ]

        quick_channels = channels[:8]
        my_creators = creators[:12]

        context["summary"] = {
            "creator_count": len(creators),
            "channel_count": len(channels),
            "assignment_count": len(assignments),
            "needs_reset_count": len(channels_needing_reset),
            "without_2fa_count": len(channels_without_2fa),
            "vpn_gap_count": len(vpn_policy_gaps),
            "consent_issue_count": len(consent_issues),
        }

        context["channels_needing_reset"] = channels_needing_reset[:10]
        context["channels_without_2fa"] = channels_without_2fa[:10]
        context["vpn_policy_gaps"] = vpn_policy_gaps[:10]
        context["consent_issues"] = consent_issues[:10]
        context["paused_or_offboarded"] = paused_or_offboarded[:10]
        context["creators_without_active_assignment"] = creators_without_active_assignment[
            :10
        ]
        context["quick_channels"] = quick_channels
        context["my_creators"] = my_creators

        return context


class CreatorListView(LoginRequiredMixin, ScopedCreatorQuerysetMixin, ListView):
    model = Creator
    template_name = "creators/creator_list.html"
    context_object_name = "creators"

    @classmethod
    def request_scoped_queryset(cls, request):
        view = cls()
        view.request = request
        return view.get_queryset()


class CreatorDetailView(
    LoginRequiredMixin,
    ScopedCreatorQuerysetMixin,
    ScopedCreatorObjectMixin,
    DetailView,
):
    model = Creator
    template_name = "creators/creator_detail.html"
    context_object_name = "creator"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        creator = self.object

        channels = list(
            scope_channels_queryset(
                self.request.user,
                qs=CreatorChannel.objects.select_related("creator"),
            ).filter(creator=creator)
        )

        assignments = list(
            scope_assignments_queryset(
                self.request.user,
                qs=OperatorAssignment.objects.select_related(
                    "operator",
                    "operator__user",
                    "creator",
                ),
            ).filter(creator=creator)
        )

        needs_reset = [
            channel for channel in channels if channel.credential_status == "needs_reset"
        ]
        without_2fa = [
            channel for channel in channels if not channel.two_factor_enabled
        ]
        vpn_required = [channel for channel in channels if channel.vpn_required]
        policy_gaps = [
            channel
            for channel in channels
            if channel.vpn_required
            and not (channel.approved_ip_label or channel.approved_egress_ip)
        ]

        context["channels"] = channels
        context["assignments"] = assignments

        context["summary"] = {
            "channel_count": len(channels),
            "assignment_count": len(assignments),
            "needs_reset_count": len(needs_reset),
            "without_2fa_count": len(without_2fa),
            "vpn_required_count": len(vpn_required),
            "policy_gap_count": len(policy_gaps),
        }

        context["alerts"] = {
            "needs_reset": needs_reset,
            "without_2fa": without_2fa,
            "vpn_required": vpn_required,
            "policy_gaps": policy_gaps,
        }

        return context


class CreatorNetworkView(
    LoginRequiredMixin,
    ScopedCreatorQuerysetMixin,
    ScopedCreatorObjectMixin,
    DetailView,
):
    model = Creator
    template_name = "creators/creator_network.html"
    context_object_name = "creator"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        creator = self.object

        channels = scope_channels_queryset(
            self.request.user,
            qs=CreatorChannel.objects.select_related("creator"),
        ).filter(creator=creator)

        assignments = scope_assignments_queryset(
            self.request.user,
            qs=OperatorAssignment.objects.select_related(
                "operator",
                "operator__user",
                "creator",
            ),
        ).filter(creator=creator)

        nodes = []
        edges = []

        creator_node_id = f"creator-{creator.pk}"
        creator_color = "#2563eb"
        if creator.status != "active" or creator.consent_status != "active":
            creator_color = "#f59e0b"

        nodes.append(
            {
                "id": creator_node_id,
                "label": creator.display_name,
                "shape": "box",
                "color": creator_color,
            }
        )

        if creator.primary_operator:
            operator = creator.primary_operator
            operator_id = f"operator-primary-{operator.pk}"
            nodes.append(
                {
                    "id": operator_id,
                    "label": f"Primary: {operator}",
                    "shape": "ellipse",
                    "color": "#16a34a",
                }
            )
            edges.append(
                {
                    "from": creator_node_id,
                    "to": operator_id,
                    "label": "primary_operator",
                }
            )

        seen_assignment_operators = set()
        for assignment in assignments:
            operator = assignment.operator
            operator_id = f"operator-{operator.pk}"

            if operator_id not in seen_assignment_operators:
                nodes.append(
                    {
                        "id": operator_id,
                        "label": f"{operator}\n{assignment.scope}",
                        "shape": "ellipse",
                        "color": "#22c55e",
                    }
                )
                seen_assignment_operators.add(operator_id)

            edges.append(
                {
                    "from": operator_id,
                    "to": creator_node_id,
                    "label": assignment.scope,
                }
            )

        for channel in channels:
            channel_id = f"channel-{channel.pk}"
            channel_color = "#7c3aed"

            if channel.credential_status == "needs_reset":
                channel_color = "#dc2626"
            elif not channel.two_factor_enabled:
                channel_color = "#f59e0b"

            nodes.append(
                {
                    "id": channel_id,
                    "label": f"{channel.platform}\n{channel.handle}",
                    "shape": "dot",
                    "size": 22,
                    "color": channel_color,
                }
            )
            edges.append(
                {
                    "from": creator_node_id,
                    "to": channel_id,
                    "label": channel.access_mode,
                }
            )

        context["network_nodes"] = nodes
        context["network_edges"] = edges
        return context


class CreatorCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = Creator
    form_class = CreatorForm
    template_name = "creators/creator_form.html"
    success_url = reverse_lazy("creator-list")


class CreatorUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Creator
    form_class = CreatorForm
    template_name = "creators/creator_form.html"

    def get_success_url(self):
        return reverse_lazy("creator-detail", kwargs={"pk": self.object.pk})


class ChannelListView(LoginRequiredMixin, ScopedChannelQuerysetMixin, ListView):
    model = CreatorChannel
    template_name = "channels/channel_list.html"
    context_object_name = "channels"

    PRESET_LABELS = {
        "all": "Alle channels",
        "issues": "Alle issues",
        "needs_reset": "Needs reset",
        "no_2fa": "Geen 2FA",
        "vpn_gap": "VPN gaps",
        "no_identifier": "Geen identifier",
        "no_update": "Geen update",
    }

    @staticmethod
    def issue_q():
        return (
            Q(credential_status="needs_reset")
            | Q(two_factor_enabled=False)
            | (
                Q(vpn_required=True)
                & Q(approved_ip_label="")
                & Q(approved_egress_ip="")
            )
            | (
                Q(login_identifier="")
                & Q(account_email="")
                & Q(account_phone_number="")
            )
            | Q(last_operator_update="")
        )

    @staticmethod
    def preset_q(preset):
        if preset == "issues":
            return ChannelListView.issue_q()
        if preset == "needs_reset":
            return Q(credential_status="needs_reset")
        if preset == "no_2fa":
            return Q(two_factor_enabled=False)
        if preset == "vpn_gap":
            return (
                Q(vpn_required=True)
                & Q(approved_ip_label="")
                & Q(approved_egress_ip="")
            )
        if preset == "no_identifier":
            return (
                Q(login_identifier="")
                & Q(account_email="")
                & Q(account_phone_number="")
            )
        if preset == "no_update":
            return Q(last_operator_update="")
        return Q()

    @staticmethod
    def mark_issue_flags(channel):
        channel.policy_gap = (
            channel.vpn_required
            and not channel.approved_ip_label
            and not channel.approved_egress_ip
        )
        channel.missing_identifier = (
            not channel.login_identifier
            and not channel.account_email
            and not channel.account_phone_number
        )
        channel.missing_update = not bool((channel.last_operator_update or "").strip())
        channel.has_issue = any(
            [
                channel.credential_status == "needs_reset",
                not channel.two_factor_enabled,
                channel.policy_gap,
                channel.missing_identifier,
                channel.missing_update,
            ]
        )
        return channel

    def get_current_preset(self):
        preset = (self.request.GET.get("preset") or "").strip()
        legacy_issues_only = (self.request.GET.get("issues_only") or "").strip()

        if not preset and legacy_issues_only == "yes":
            preset = "issues"

        if preset not in self.PRESET_LABELS:
            preset = "all"

        return preset

    def get_queryset(self):
        qs = super().get_queryset().select_related("creator")

        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        credential_status = (self.request.GET.get("credential_status") or "").strip()
        two_factor_enabled = (self.request.GET.get("two_factor_enabled") or "").strip()
        vpn_required = (self.request.GET.get("vpn_required") or "").strip()
        preset = self.get_current_preset()

        if q:
            qs = qs.filter(
                Q(creator__display_name__icontains=q)
                | Q(handle__icontains=q)
                | Q(login_identifier__icontains=q)
                | Q(account_email__icontains=q)
                | Q(account_phone_number__icontains=q)
            )

        if status:
            qs = qs.filter(status=status)

        if credential_status:
            qs = qs.filter(credential_status=credential_status)

        if two_factor_enabled == "yes":
            qs = qs.filter(two_factor_enabled=True)
        elif two_factor_enabled == "no":
            qs = qs.filter(two_factor_enabled=False)

        if vpn_required == "yes":
            qs = qs.filter(vpn_required=True)
        elif vpn_required == "no":
            qs = qs.filter(vpn_required=False)

        if preset != "all":
            qs = qs.filter(self.preset_q(preset))

        qs = qs.order_by(
            F("last_operator_update_at").desc(nulls_last=True),
            "creator__display_name",
            "handle",
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        channels = list(context["channels"])
        channels = [self.mark_issue_flags(channel) for channel in channels]
        context["channels"] = channels

        base_scoped_qs = super().get_queryset().select_related("creator")

        preset_counts = {
            "all": base_scoped_qs.count(),
            "issues": base_scoped_qs.filter(self.preset_q("issues")).count(),
            "needs_reset": base_scoped_qs.filter(self.preset_q("needs_reset")).count(),
            "no_2fa": base_scoped_qs.filter(self.preset_q("no_2fa")).count(),
            "vpn_gap": base_scoped_qs.filter(self.preset_q("vpn_gap")).count(),
            "no_identifier": base_scoped_qs.filter(self.preset_q("no_identifier")).count(),
            "no_update": base_scoped_qs.filter(self.preset_q("no_update")).count(),
        }

        context["channel_status_choices"] = CreatorChannel.Status.choices
        context["credential_status_choices"] = CreatorChannel.CredentialStatus.choices
        context["current_q"] = (self.request.GET.get("q") or "").strip()
        context["current_status"] = (self.request.GET.get("status") or "").strip()
        context["current_credential_status"] = (
            self.request.GET.get("credential_status") or ""
        ).strip()
        context["current_two_factor_enabled"] = (
            self.request.GET.get("two_factor_enabled") or ""
        ).strip()
        context["current_vpn_required"] = (
            self.request.GET.get("vpn_required") or ""
        ).strip()
        context["current_updated"] = (self.request.GET.get("updated") or "").strip()
        context["current_full_path"] = self.request.get_full_path()
        context["current_preset"] = self.get_current_preset()
        context["preset_labels"] = self.PRESET_LABELS
        context["preset_counts"] = preset_counts

        context["visible_count"] = len(channels)
        context["issue_count"] = sum(1 for channel in channels if channel.has_issue)

        return context


class ChannelDetailView(LoginRequiredMixin, ScopedChannelQuerysetMixin, DetailView):
    model = CreatorChannel
    template_name = "channels/channel_detail.html"
    context_object_name = "channel"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel = self.object
        creator = channel.creator
        next_url = get_safe_next_url(self.request)

        assignments = list(
            scope_assignments_queryset(
                self.request.user,
                qs=OperatorAssignment.objects.select_related(
                    "operator",
                    "operator__user",
                    "creator",
                ),
            ).filter(creator=creator)
        )

        policy_gap = channel.vpn_required and not (
            channel.approved_ip_label or channel.approved_egress_ip
        )
        handoff_missing = not bool((channel.last_operator_update or "").strip())

        context["creator"] = creator
        context["assignments"] = assignments
        context["policy_gap"] = policy_gap
        context["handoff_missing"] = handoff_missing
        context["next_url"] = next_url
        context["back_to_queue_url"] = next_url or reverse("channel-list")

        return context


class ChannelFormNavigationMixin:
    def get_next_url(self):
        return get_safe_next_url(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_url = self.get_next_url()
        context["next_url"] = next_url
        context["back_to_queue_url"] = next_url or reverse("channel-list")
        return context

    def get_fallback_success_url(self):
        return reverse("channel-update", kwargs={"pk": self.object.pk}) + "?saved=1"

    def get_success_url(self):
        next_url = self.get_next_url()
        if next_url:
            return append_query_parameter(next_url, "updated", "1")
        return self.get_fallback_success_url()


class CreatorChannelCreateView(
    LoginRequiredMixin,
    AdminOnlyMixin,
    ChannelFormNavigationMixin,
    CreateView,
):
    model = CreatorChannel
    form_class = CreatorChannelForm
    template_name = "channels/channel_form.html"

    def form_valid(self, form):
        update_text = (form.cleaned_data.get("last_operator_update") or "").strip()
        if update_text:
            form.instance.last_operator_update_at = timezone.now()
        else:
            form.instance.last_operator_update_at = None
        return super().form_valid(form)


class CreatorChannelUpdateView(
    LoginRequiredMixin,
    AdminOnlyMixin,
    ChannelFormNavigationMixin,
    UpdateView,
):
    model = CreatorChannel
    form_class = CreatorChannelForm
    template_name = "channels/channel_form.html"

    def form_valid(self, form):
        if "last_operator_update" in form.changed_data:
            update_text = (form.cleaned_data.get("last_operator_update") or "").strip()
            if update_text:
                form.instance.last_operator_update_at = timezone.now()
            else:
                form.instance.last_operator_update_at = None

        return super().form_valid(form)


class AssignmentListView(LoginRequiredMixin, ScopedAssignmentQuerysetMixin, ListView):
    model = OperatorAssignment
    template_name = "assignments/assignment_list.html"
    context_object_name = "assignments"


class OperatorAssignmentCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = OperatorAssignment
    form_class = OperatorAssignmentForm
    template_name = "assignments/assignment_form.html"
    success_url = reverse_lazy("assignment-list")


class OperatorAssignmentUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = OperatorAssignment
    form_class = OperatorAssignmentForm
    template_name = "assignments/assignment_form.html"
    success_url = reverse_lazy("assignment-list")


class OperatorListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    model = Operator
    template_name = "operators/operator_list.html"
    context_object_name = "operators"
    queryset = Operator.objects.select_related("user")