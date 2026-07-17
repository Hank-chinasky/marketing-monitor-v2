from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.forms import ConversationThreadForm
from core.models import BuddyDraft, ConversationThread
from core.services.demo_access import is_demo_viewer
from core.services.scope import get_creator_queryset_for_user


def get_scoped_conversation_thread_queryset(user):
    creator_ids = get_creator_queryset_for_user(user).values("pk")
    return (
        ConversationThread.objects.select_related("creator", "channel")
        .filter(creator_id__in=creator_ids)
    )


def get_scoped_buddy_draft_queryset(user):
    creator_ids = get_creator_queryset_for_user(user).values("pk")
    return (
        BuddyDraft.objects.select_related("thread", "thread__creator", "thread__channel")
        .filter(thread__creator_id__in=creator_ids)
    )


def get_latest_buddy_draft(thread):
    return thread.buddy_drafts.order_by("-created_at", "-id").first()


class ConversationThreadListView(LoginRequiredMixin, ListView):
    model = ConversationThread
    template_name = "conversations/conversation_thread_list.html"
    context_object_name = "threads"

    def get_queryset(self):
        return get_scoped_conversation_thread_queryset(self.request.user).order_by(
            "-last_message_at",
            "-id",
        )


class ConversationThreadDetailView(LoginRequiredMixin, DetailView):
    model = ConversationThread
    template_name = "conversations/conversation_thread_detail.html"
    context_object_name = "thread"

    def get_queryset(self):
        return get_scoped_conversation_thread_queryset(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_draft = get_latest_buddy_draft(self.object)
        context["latest_draft"] = latest_draft
        context["demo_read_only"] = is_demo_viewer(self.request.user)
        context["can_approve_latest_draft"] = bool(
            not context["demo_read_only"]
            and latest_draft
            and latest_draft.state == BuddyDraft.State.DRAFTED
        )
        return context


class ConversationThreadManualIntakeMixin:
    model = ConversationThread
    form_class = ConversationThreadForm
    template_name = "conversations/conversation_thread_form.html"

    def dispatch(self, request, *args, **kwargs):
        if is_demo_viewer(request.user):
            raise PermissionDenied("Demo viewer access is read-only.")

        if not get_creator_queryset_for_user(request.user).exists():
            raise PermissionDenied("No scoped creator access for manual thread intake.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("conversation-thread-detail", kwargs={"pk": self.object.pk})


class ConversationThreadCreateView(
    LoginRequiredMixin,
    ConversationThreadManualIntakeMixin,
    CreateView,
):
    pass


class ConversationThreadUpdateView(
    LoginRequiredMixin,
    ConversationThreadManualIntakeMixin,
    UpdateView,
):
    def get_queryset(self):
        return get_scoped_conversation_thread_queryset(self.request.user)


class BuddyDraftApproveView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk, *args, **kwargs):
        if is_demo_viewer(request.user):
            raise PermissionDenied("Demo viewer access is read-only.")

        draft = get_object_or_404(
            get_scoped_buddy_draft_queryset(request.user).filter(
                state=BuddyDraft.State.DRAFTED
            ),
            pk=pk,
        )
        latest_draft = get_latest_buddy_draft(draft.thread)
        if latest_draft is None or latest_draft.pk != draft.pk:
            raise Http404("No BuddyDraft matches the given query.")

        draft.state = BuddyDraft.State.APPROVED
        draft.approved_at = timezone.now()
        draft.approved_by_user = request.user
        draft.save(update_fields=["state", "approved_at", "approved_by_user"])

        return redirect("conversation-thread-detail", pk=draft.thread.pk)
