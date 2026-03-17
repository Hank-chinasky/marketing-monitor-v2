from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

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


class CreatorListView(LoginRequiredMixin, ScopedCreatorQuerysetMixin, ListView):
    model = Creator
    template_name = "creators/creator_list.html"
    context_object_name = "creators"


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
        context["channels"] = scope_channels_queryset(
            self.request.user,
            qs=CreatorChannel.objects.select_related("creator"),
        ).filter(creator=creator)
        context["assignments"] = scope_assignments_queryset(
            self.request.user,
            qs=OperatorAssignment.objects.select_related("operator", "operator__user", "creator"),
        ).filter(creator=creator)
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
