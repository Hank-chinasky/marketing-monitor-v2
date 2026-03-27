from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View

from core.mixins import AdminOnlyMixin
from core.models import OperatorAssignment
from core.services.scope import is_admin_user
from core.views import AssignmentListView as BaseAssignmentListView


class AssignmentListView(BaseAssignmentListView):
    def get_queryset(self):
        return super().get_queryset().select_related(
            "operator",
            "operator__user",
            "creator",
        ).order_by("-active", "creator__display_name", "operator__user__username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignments = list(context["assignments"])
        context["assignments"] = assignments
        context["can_manage_assignments"] = is_admin_user(self.request.user)
        context["saved"] = self.request.GET.get("saved") == "1"
        context["status_changed"] = self.request.GET.get("status_changed") == "1"
        context["summary"] = {
            "assignment_count": len(assignments),
            "active_count": sum(1 for assignment in assignments if assignment.active),
            "inactive_count": sum(1 for assignment in assignments if not assignment.active),
        }
        return context


class OperatorAssignmentDeactivateView(LoginRequiredMixin, AdminOnlyMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        assignment = get_object_or_404(OperatorAssignment, pk=kwargs["pk"])
        if assignment.active:
            assignment.active = False
            assignment.save(update_fields=["active"])

        redirect_url = reverse("assignment-list")
        redirect_url = f"{redirect_url}?status_changed=1"
        return HttpResponseRedirect(redirect_url)
