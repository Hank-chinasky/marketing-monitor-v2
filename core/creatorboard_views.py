from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, IntegerField, Value, When
from django.views.generic import DetailView, ListView

from core.models import CreatorBoardWorkItem
from core.services.scope import is_admin_user


def get_creatorboard_workitem_queryset_for_user(user):
    base_qs = CreatorBoardWorkItem.objects.select_related("assigned_to")

    if is_admin_user(user):
        return base_qs

    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return base_qs.none()

    return base_qs.filter(assigned_to=user)


class CreatorBoardQueueView(LoginRequiredMixin, ListView):
    model = CreatorBoardWorkItem
    template_name = "core/creatorboard/queue.html"
    context_object_name = "workitems"
    paginate_by = 50

    def get_queryset(self):
        return (
            get_creatorboard_workitem_queryset_for_user(self.request.user)
            .annotate(
                priority_rank=Case(
                    When(priority=CreatorBoardWorkItem.Priority.HIGH, then=Value(0)),
                    When(priority=CreatorBoardWorkItem.Priority.MEDIUM, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
            .order_by("priority_rank", "-updated_at", "-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["queue_title"] = "CreatorBoard work queue"
        context["queue_subtitle"] = "Fase 1A basis zonder live routing of dashboard-entry."
        return context


class CreatorBoardDetailView(LoginRequiredMixin, DetailView):
    model = CreatorBoardWorkItem
    template_name = "core/creatorboard/detail.html"
    context_object_name = "workitem"

    def get_queryset(self):
        return get_creatorboard_workitem_queryset_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = None
        context["detail_title"] = "CreatorBoard work item"
        return context