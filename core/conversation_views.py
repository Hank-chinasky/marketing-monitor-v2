from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from core.models import ConversationThread
from core.services.scope import get_creator_queryset_for_user


class ConversationThreadListView(LoginRequiredMixin, ListView):
    model = ConversationThread
    template_name = "conversations/conversation_thread_list.html"
    context_object_name = "threads"

    def get_queryset(self):
        creator_ids = get_creator_queryset_for_user(self.request.user).values("pk")
        return (
            ConversationThread.objects
            .select_related("creator", "channel")
            .filter(creator_id__in=creator_ids)
            .order_by("-last_message_at", "-id")
        )


class ConversationThreadDetailView(LoginRequiredMixin, DetailView):
    model = ConversationThread
    template_name = "conversations/conversation_thread_detail.html"
    context_object_name = "thread"

    def get_queryset(self):
        creator_ids = get_creator_queryset_for_user(self.request.user).values("pk")
        return (
            ConversationThread.objects
            .select_related("creator", "channel")
            .filter(creator_id__in=creator_ids)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["latest_draft"] = self.object.buddy_drafts.order_by(
            "-created_at",
            "-id",
        ).first()
        return context
