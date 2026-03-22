from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
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


class HealthzView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok"})


class OperationsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/operations_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        creators = list(
            CreatorListView.request_scoped_queryset(self.request).select_related("primary_operator")
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
                qs=OperatorAssignment.objects.select_related("creator", "operator", "operator__user"),
            )
        )

        channels_needing_reset = [c for c in channels if c.credential_status == "needs_reset"]
        channels_without_2fa = [c for c in channels if not c.two_factor_enabled]
        vpn_policy_gaps = [
            c for c in channels
            if c.vpn_required and not (c.approved_ip_label or c.approved_egress_ip)
        ]
        consent_issues = [c for c in creators if c.consent_status != "active"]
        paused_or_offboarded = [c for c in creators if c.status != "active"]

        assigned_creator_ids = {a.creator_id for a in assignments}
        creators_without_active_assignment = [
            c for c in creators if c.pk not in assigned_creator_ids
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
        context["creators_without_active_assignment"] = creators_without_active_assignment[:10]
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
                qs=OperatorAssignment.objects.select_related("operator", "operator__user", "creator"),
            ).filter(creator=creator)
        )

        needs_reset = [c for c in channels if c.credential_status == "needs_reset"]
        without_2fa = [c for c in channels if not c.two_factor_enabled]
        vpn_required = [c for c in channels if c.vpn_required]
        policy_gaps = [
            c for c in channels
            if c.vpn_required and not (c.approved_ip_label or c.approved_egress_ip)
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
            qs=OperatorAssignment.objects.select_related("operator", "operator__user", "creator"),
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
            op_id = f"operator-primary-{operator.pk}"
            nodes.append(
                {
                    "id": op_id,
                    "label": f"Primary: {operator}",
                    "shape": "ellipse",
                    "color": "#16a34a",
                }
            )
            edges.append(
                {
                    "from": creator_node_id,
                    "to": op_id,
                    "label": "primary_operator",
                }
            )

        seen_assignment_ops = set()
        for assignment in assignments:
            op = assignment.operator
            op_id = f"operator-{op.pk}"

            if op_id not in seen_assignment_ops:
                nodes.append(
                    {
                        "id": op_id,
                        "label": f"{op}\n{assignment.scope}",
                        "shape": "ellipse",
                        "color": "#22c55e",
                    }
                )
                seen_assignment_ops.add(op_id)

            edges.append(
                {
                    "from": op_id,
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


class ChannelDetailView(LoginRequiredMixin, ScopedChannelQuerysetMixin, DetailView):
    model = CreatorChannel
    template_name = "channels/channel_detail.html"
    context_object_name = "channel"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel = self.object
        creator = channel.creator

        assignments = list(
            scope_assignments_queryset(
                self.request.user,
                qs=OperatorAssignment.objects.select_related("operator", "operator__user", "creator"),
            ).filter(creator=creator)
        )

        policy_gap = channel.vpn_required and not (
            channel.approved_ip_label or channel.approved_egress_ip
        )

        context["creator"] = creator
        context["assignments"] = assignments
        context["policy_gap"] = policy_gap

        return context


class CreatorChannelCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = CreatorChannel
    form_class = CreatorChannelForm
    template_name = "channels/channel_form.html"
    success_url = reverse_lazy("channel-list")


class CreatorChannelUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = CreatorChannel
    form_class = CreatorChannelForm
    template_name = "channels/channel_form.html"
    success_url = reverse_lazy("channel-list")


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