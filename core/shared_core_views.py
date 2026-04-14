from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from core.conversation_views import get_latest_buddy_draft, get_scoped_conversation_thread_queryset
from core.models import ConversationThread, CreatorMaterial, OperatorAssignment
from core.services.scope import (
    get_active_assignments_for_operator,
    get_channel_queryset_for_user,
    get_creator_queryset_for_user,
    get_operator_for_user,
)


def get_active_assignment_for_user_and_creator(user, creator):
    if not creator:
        return None

    operator = get_operator_for_user(user)
    if not operator:
        return None

    return (
        get_active_assignments_for_operator(operator)
        .filter(creator=creator)
        .order_by("-starts_at", "-id")
        .first()
    )


def build_assignment_context(assignment):
    if not assignment:
        return {
            "has_active_assignment": False,
            "status_label": "geen actieve assignment",
            "scope_label": "-",
        }

    return {
        "has_active_assignment": True,
        "status_label": "actieve assignment",
        "scope_label": assignment.get_scope_display(),
    }


class ChatHubView(LoginRequiredMixin, TemplateView):
    template_name = "chats/chat_hub.html"

    def _build_completeness_alerts(self, selected_thread):
        if not selected_thread:
            return ["Geen actieve thread geselecteerd."]

        alerts = []
        creator = selected_thread.creator
        channel = selected_thread.channel

        if creator.consent_status != creator.ConsentStatus.ACTIVE:
            alerts.append("Creator consent staat niet op actief.")
        if not channel:
            alerts.append("Geen channel gekoppeld aan deze thread.")
        if not selected_thread.guardrails:
            alerts.append("Guardrails ontbreken; policy-context is onvolledig.")
        if not selected_thread.open_loop:
            alerts.append("Volgende stap ontbreekt (open loop leeg).")
        if not selected_thread.last_handoff_note:
            alerts.append("Laatste handoff-status ontbreekt.")

        return alerts

    def _build_access_state(self, selected_thread, assignment):
        if not selected_thread:
            return {
                "status": "blocked",
                "label": "blocked",
                "badge": "badge-red",
                "reason": "Geen actieve thread geselecteerd; start hier geen operatoractie.",
            }

        if not assignment:
            return {
                "status": "blocked",
                "label": "blocked",
                "badge": "badge-red",
                "reason": "Geen actieve operator-assignment voor deze creator.",
            }

        if assignment.scope not in {
            OperatorAssignment.Scope.FULL_MANAGEMENT,
            OperatorAssignment.Scope.DRAFT_ONLY,
        }:
            return {
                "status": "blocked",
                "label": "blocked",
                "badge": "badge-red",
                "reason": "Assignment-scope laat geen chat-operatoractie toe.",
            }

        completeness_alerts = self._build_completeness_alerts(selected_thread)
        if (
            "Geen channel gekoppeld aan deze thread." in completeness_alerts
            or "Guardrails ontbreken; policy-context is onvolledig." in completeness_alerts
        ):
            return {
                "status": "blocked",
                "label": "blocked",
                "badge": "badge-red",
                "reason": "Essentiële context/policy ontbreekt; eerst aanvullen of escaleren.",
            }

        if (
            selected_thread.creator.consent_status != selected_thread.creator.ConsentStatus.ACTIVE
            or bool(selected_thread.risk_flags)
            or "Volgende stap ontbreekt (open loop leeg)." in completeness_alerts
            or "Laatste handoff-status ontbreekt." in completeness_alerts
        ):
            return {
                "status": "review_needed",
                "label": "review_needed",
                "badge": "badge-yellow",
                "reason": "Context is deels aanwezig, maar review nodig vóór operatoractie.",
            }

        return {
            "status": "allowed",
            "label": "allowed",
            "badge": "badge-green",
            "reason": "Thread/context/policy en operator-scope zijn voldoende voor actie.",
        }

    def _get_threads(self):
        return list(
            get_scoped_conversation_thread_queryset(self.request.user)
            .select_related("creator", "channel")
            .order_by("-last_message_at", "-id")
        )

    def _resolve_selected_thread(self, threads, *, source="get", fallback_to_first=True):
        selected_thread = None
        selected_thread_param = ""

        if source == "post":
            selected_thread_param = (self.request.POST.get("thread") or "").strip()
        else:
            selected_thread_param = (self.request.GET.get("thread") or "").strip()

        if selected_thread_param.isdigit():
            selected_thread = next(
                (thread for thread in threads if thread.pk == int(selected_thread_param)),
                None,
            )

        if selected_thread is None and fallback_to_first and threads:
            selected_thread = threads[0]

        return selected_thread


    def _build_handoff_form_data(self, selected_thread, posted_values=None):
        if posted_values is not None:
            return {
                "handoff_summary": posted_values.get("handoff_summary", ""),
                "next_step": posted_values.get("next_step", ""),
                "blocker": posted_values.get("blocker", ""),
                "close_signal": posted_values.get("close_signal", "overdracht_klaar") or "overdracht_klaar",
            }

        return {
            "handoff_summary": "",
            "next_step": selected_thread.open_loop if selected_thread and selected_thread.open_loop else "",
            "blocker": "",
            "close_signal": "overdracht_klaar",
        }

    def _build_context(
        self,
        *,
        submit_error="",
        handoff_form_data=None,
        thread_source="get",
        fallback_to_first=True,
    ):
        threads = self._get_threads()
        selected_thread = self._resolve_selected_thread(
            threads,
            source=thread_source,
            fallback_to_first=fallback_to_first,
        )

        assignment = get_active_assignment_for_user_and_creator(
            self.request.user,
            selected_thread.creator if selected_thread else None,
        )
        access_state = self._build_access_state(selected_thread, assignment)
        latest_draft = get_latest_buddy_draft(selected_thread) if selected_thread else None

        run_log = []
        open_issues = []
        quick_actions = []

        if selected_thread:
            run_log.append(
                {
                    "label": "Laatste bericht",
                    "value": selected_thread.last_message_at or "-",
                }
            )
            run_log.append(
                {
                    "label": "Laatste operator handoff",
                    "value": selected_thread.last_operator_handoff_at or "-",
                }
            )
            if latest_draft:
                run_log.append(
                    {
                        "label": "Laatste BuddyDraft",
                        "value": f"{latest_draft.get_state_display()} ({latest_draft.created_at})",
                    }
                )

            if selected_thread.risk_flags:
                open_issues.append(selected_thread.risk_flags)
            if selected_thread.open_loop:
                open_issues.append(f"Open loop: {selected_thread.open_loop}")
            if latest_draft and latest_draft.requires_human_attention:
                open_issues.append("BuddyDraft vereist human attention.")

            quick_actions.append(
                {
                    "label": "Open thread detail",
                    "url": f"/conversations/{selected_thread.pk}/",
                }
            )
            if latest_draft and latest_draft.state == latest_draft.State.DRAFTED:
                quick_actions.append(
                    {
                        "label": "Draft goedkeuren",
                        "type": "approve",
                        "draft_id": latest_draft.pk,
                    }
                )

        return {
            "threads": threads,
            "selected_thread": selected_thread,
            "latest_draft": latest_draft,
            "completeness_alerts": self._build_completeness_alerts(selected_thread),
            "assignment_context": build_assignment_context(assignment),
            "access_state": access_state,
            "run_log": run_log,
            "open_issues": open_issues,
            "quick_actions": quick_actions,
            "saved": self.request.GET.get("saved") == "1",
            "submit_error": submit_error,
            "handoff_form": self._build_handoff_form_data(
                selected_thread,
                handoff_form_data,
            ),
        }

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self._build_context(thread_source="get", fallback_to_first=True))

    def post(self, request, *args, **kwargs):
        posted_values = {
            "handoff_summary": (request.POST.get("handoff_summary") or "").strip(),
            "next_step": (request.POST.get("next_step") or "").strip(),
            "blocker": (request.POST.get("blocker") or "").strip(),
            "close_signal": (request.POST.get("close_signal") or "").strip() or "overdracht_klaar",
        }
        context = self._build_context(
            handoff_form_data=posted_values,
            thread_source="post",
            fallback_to_first=False,
        )
        selected_thread = context["selected_thread"]

        if not selected_thread:
            context["submit_error"] = "Geen actieve thread geselecteerd voor handoff-afsluiting."
            return self.render_to_response(context)

        if context["access_state"]["status"] == "blocked":
            context["submit_error"] = "Handoff afsluiten is geblokkeerd: los eerst access/context issues op."
            return self.render_to_response(context)

        handoff_summary = posted_values["handoff_summary"]
        next_step = posted_values["next_step"]
        blocker = posted_values["blocker"]
        close_signal = posted_values["close_signal"]

        if not handoff_summary or not next_step:
            context["submit_error"] = "Laatste stand en volgende stap zijn verplicht om af te sluiten."
            return self.render_to_response(context)

        selected_thread.last_handoff_note = (
            f"Laatste stand: {handoff_summary}\n"
            f"Volgende stap: {next_step}\n"
            f"Blocker/issue: {blocker or '-'}\n"
            f"Afsluitsignaal: {close_signal}"
        )
        selected_thread.open_loop = next_step
        selected_thread.last_operator_handoff_at = timezone.now()
        selected_thread.save(
            update_fields=[
                "last_handoff_note",
                "open_loop",
                "last_operator_handoff_at",
            ]
        )

        query = urlencode({"thread": selected_thread.pk, "saved": 1})
        return redirect(f"{reverse('chat-hub')}?{query}")


class FeederHubView(LoginRequiredMixin, TemplateView):
    template_name = "feeder/feeder_hub.html"

    def _build_completeness_alerts(self, selected_creator, channels, materials):
        if not selected_creator:
            return ["Geen creator geselecteerd."]

        alerts = []

        if selected_creator.consent_status != selected_creator.ConsentStatus.ACTIVE:
            alerts.append("Creator consent staat niet op actief.")
        if not selected_creator.content_source_url:
            alerts.append("Content source URL ontbreekt.")
        if not selected_creator.content_ready_status:
            alerts.append("Content ready status ontbreekt.")
        if not channels:
            alerts.append("Geen channels gekoppeld binnen scope.")
        if not materials:
            alerts.append("Geen actief materiaal beschikbaar in feeder.")

        channel_with_next_step = any(channel.session_next_action for channel in channels)
        if not channel_with_next_step:
            alerts.append("Volgende stap ontbreekt in channel sessiecontext.")

        return alerts

    def _build_access_state(self, selected_creator, assignment, channels):
        if not selected_creator:
            return {
                "status": "blocked",
                "label": "blocked",
                "badge": "badge-red",
                "reason": "Geen creator geselecteerd; feederactie is geblokkeerd.",
            }

        if not assignment:
            return {
                "status": "blocked",
                "label": "blocked",
                "badge": "badge-red",
                "reason": "Geen actieve operator-assignment voor deze creator.",
            }

        if not channels or not selected_creator.content_source_url:
            return {
                "status": "blocked",
                "label": "blocked",
                "badge": "badge-red",
                "reason": "Werkbare basiscontext ontbreekt (channel of content source).",
            }

        if assignment.scope not in {
            OperatorAssignment.Scope.FULL_MANAGEMENT,
            OperatorAssignment.Scope.POSTING_ONLY,
        }:
            return {
                "status": "review_needed",
                "label": "review_needed",
                "badge": "badge-yellow",
                "reason": "Assignment scope vraagt review voor feeder-acties.",
            }

        if (
            selected_creator.consent_status != selected_creator.ConsentStatus.ACTIVE
            or selected_creator.content_ready_status
            != selected_creator.ContentReadyStatus.READY_TO_POST
        ):
            return {
                "status": "review_needed",
                "label": "review_needed",
                "badge": "badge-yellow",
                "reason": "Consent/readiness vraagt extra review vóór live actie.",
            }

        return {
            "status": "allowed",
            "label": "allowed",
            "badge": "badge-green",
            "reason": "Creator/context/operator-scope voldoende om binnen Feeder te werken.",
        }

    def _select_latest_handoff_channel(self, channels):
        if not channels:
            return None

        return max(
            channels,
            key=lambda channel: (
                channel.session_updated_at is not None,
                channel.session_updated_at,
                channel.pk,
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        creators = list(
            get_creator_queryset_for_user(self.request.user)
            .select_related("primary_operator")
            .order_by("display_name")
        )
        channels_qs = get_channel_queryset_for_user(self.request.user).select_related("creator")

        selected_creator = None
        selected_creator_param = (self.request.GET.get("creator") or "").strip()
        if selected_creator_param.isdigit():
            selected_creator = next(
                (creator for creator in creators if creator.pk == int(selected_creator_param)),
                None,
            )
        if selected_creator is None and creators:
            selected_creator = creators[0]

        materials = []
        channels = []
        creator_threads = []
        open_signals = []
        run_log = []
        quick_actions = []

        assignment = get_active_assignment_for_user_and_creator(self.request.user, selected_creator)

        if selected_creator:
            materials = list(
                CreatorMaterial.objects.filter(
                    creator=selected_creator,
                    active=True,
                )
                .select_related("uploaded_by")
                .order_by("-uploaded_at", "-id")[:30]
            )
            channels = list(channels_qs.filter(creator=selected_creator).order_by("platform", "handle"))
            creator_threads = list(
                get_scoped_conversation_thread_queryset(self.request.user)
                .filter(creator=selected_creator, active=True)
                .order_by("-last_message_at", "-id")[:20]
            )

            waiting_threads = [
                thread
                for thread in creator_threads
                if thread.status in {
                    ConversationThread.Status.WAITING_ON_OPERATOR,
                    ConversationThread.Status.HANDOFF_REQUIRED,
                }
            ]
            if waiting_threads:
                open_signals.append(
                    f"{len(waiting_threads)} thread(s) wachten op operator/handoff in Chats."
                )

            if selected_creator.content_ready_status != selected_creator.ContentReadyStatus.READY_TO_POST:
                open_signals.append("Niet alle content staat op 'ready to post'.")

            relevant_handoff_channel = self._select_latest_handoff_channel(channels)
            run_log.append(
                {
                    "label": "Laatste channel update",
                    "value": (
                        relevant_handoff_channel.session_updated_at
                        if relevant_handoff_channel
                        else "-"
                    ),
                }
            )
            run_log.append({"label": "Actief materiaal", "value": len(materials)})
            run_log.append({"label": "Open chatthreads", "value": len(waiting_threads)})

            if creator_threads:
                quick_actions.append(
                    {
                        "label": "Open Chats workspace",
                        "url": f"/chats/?thread={creator_threads[0].pk}",
                    }
                )
            if relevant_handoff_channel:
                quick_actions.append(
                    {
                        "label": "Open relevant channel",
                        "url": f"/channels/{relevant_handoff_channel.pk}/",
                    }
                )
        else:
            relevant_handoff_channel = None

        context["creators"] = creators
        context["selected_creator"] = selected_creator
        context["materials"] = materials
        context["channels"] = channels
        context["creator_threads"] = creator_threads
        context["open_signals"] = open_signals
        context["run_log"] = run_log
        context["quick_actions"] = quick_actions
        context["assignment_context"] = build_assignment_context(assignment)
        context["relevant_handoff_channel"] = relevant_handoff_channel
        context["completeness_alerts"] = self._build_completeness_alerts(
            selected_creator,
            channels,
            materials,
        )
        context["access_state"] = self._build_access_state(
            selected_creator,
            assignment,
            channels,
        )
        return context
