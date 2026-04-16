from typing import Any
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from core.conversation_views import get_latest_buddy_draft, get_scoped_conversation_thread_queryset
from core.models import Approval, ConversationThread, CreatorMaterial, OperatorAssignment
from core.services.scope import (
    get_active_assignments_for_operator,
    get_channel_queryset_for_user,
    get_creator_queryset_for_user,
    get_operator_for_user,
)

TEMPLATES_V1 = [
    {
        "id": "handoff_followup",
        "title": "Handoff follow-up update",
        "template_type": "handoff",
        "scope": "shared",
        "tags": ["handoff", "next_step", "operator"],
        "body": (
            "Hi {creator_name},\n\n"
            "Korte update via {platform} ({channel_handle}).\n"
            "Laatste overdracht: {last_handoff}.\n"
            "Volgende stap: {next_step}.\n"
            "Content ready status: {content_ready_status}."
        ),
    },
    {
        "id": "risk_review_ping",
        "title": "Risk review ping",
        "template_type": "review",
        "scope": "chats",
        "tags": ["risk", "review", "escalation"],
        "body": (
            "Creator: {creator_name}\n"
            "Platform: {platform}\n"
            "Handle: {channel_handle}\n"
            "Vraag: snelle review op risico/signaal, daarna next step: {next_step}."
        ),
    },
    {
        "id": "feeder_content_ready",
        "title": "Feeder content readiness check",
        "template_type": "feeder",
        "scope": "feeder",
        "tags": ["feeder", "content", "ready"],
        "body": (
            "Creator {creator_name}\n"
            "Status: {content_ready_status}\n"
            "Laatste handoff: {last_handoff}\n"
            "Volgende stap: {next_step}"
        ),
    },
]

TEMPLATE_ALLOWED_PLACEHOLDERS = {
    "creator_name",
    "channel_handle",
    "platform",
    "next_step",
    "last_handoff",
    "content_ready_status",
}
PLACEHOLDER_NOISE_VALUES = {"-", "n/a", "na", "none", "null", "onbekend", "geen", "tbd"}


def _safe_template_format(template_body: str, values: dict[str, str]) -> str:
    result = template_body
    for key in TEMPLATE_ALLOWED_PLACEHOLDERS:
        value = values.get(key, "")
        if value:
            result = result.replace(f"{{{key}}}", str(value))
    return result


def is_placeholder_noise(value) -> bool:
    if value is None:
        return True
    normalized = str(value).strip().lower()
    return normalized == "" or normalized in PLACEHOLDER_NOISE_VALUES


def _condense_text(value: str, *, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def build_buddy_assist_snapshot(selected_thread, completeness_alerts):
    if not selected_thread:
        return {
            "thread_summary": "Geen actieve thread geselecteerd.",
            "missing_context": ["Thread ontbreekt in selectie."],
            "next_step": "Selecteer eerst een thread.",
            "session_brief": "Geen sessiebrief beschikbaar zonder thread.",
            "condensed_handoff": "",
            "has_handoff": False,
        }

    missing_context = []
    if completeness_alerts:
        missing_context.extend(completeness_alerts)

    if is_placeholder_noise(selected_thread.thread_summary):
        missing_context.append("Threadsamenvatting ontbreekt.")
    if is_placeholder_noise(selected_thread.open_loop):
        missing_context.append("Voorgestelde volgende stap ontbreekt.")

    condensed_handoff = ""
    has_handoff = not is_placeholder_noise(selected_thread.last_handoff_note)
    if has_handoff:
        condensed_handoff = _condense_text(selected_thread.last_handoff_note, limit=220)

    session_brief_parts = [
        f"Status: {selected_thread.get_status_display()}",
        f"Bron: {selected_thread.get_source_system_display()}",
        (
            f"Laatste operator-handoff: {selected_thread.last_operator_handoff_at}"
            if selected_thread.last_operator_handoff_at
            else "Laatste operator-handoff: -"
        ),
    ]

    return {
        "thread_summary": _condense_text(selected_thread.thread_summary, limit=220)
        or "Nog geen threadsamenvatting beschikbaar.",
        "missing_context": missing_context,
        "next_step": _condense_text(selected_thread.open_loop, limit=220)
        or "Nog geen volgende stap vastgelegd.",
        "session_brief": " · ".join(session_brief_parts),
        "condensed_handoff": condensed_handoff,
        "has_handoff": has_handoff,
    }


def get_templates_for_workspace(
    workspace: str,
    *,
    query: str = "",
    template_type: str = "",
    tag: str = "",
) -> list[dict[str, Any]]:
    workspace_templates = [
        template for template in TEMPLATES_V1 if template["scope"] in {"shared", workspace}
    ]
    query_normalized = (query or "").strip().lower()
    type_normalized = (template_type or "").strip().lower()
    tag_normalized = (tag or "").strip().lower()

    def matches(template):
        if query_normalized and query_normalized not in template["title"].lower():
            return False
        if type_normalized and type_normalized != template["template_type"].lower():
            return False
        if tag_normalized and tag_normalized not in {
            item.lower() for item in template["tags"]
        }:
            return False
        return True

    return [template for template in workspace_templates if matches(template)]


def get_template_by_id_for_workspace(template_id: str, workspace: str):
    if not template_id:
        return None
    return next(
        (
            template
            for template in TEMPLATES_V1
            if template["id"] == template_id and template["scope"] in {"shared", workspace}
        ),
        None,
    )


def get_scoped_approval_queryset(user):
    return (
        Approval.objects.filter(creator__in=get_creator_queryset_for_user(user))
        .select_related("creator", "thread", "requested_by", "decided_by")
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


def append_approval_event(run_log, approvals, event_name, approval_id):
    if not str(approval_id or "").isdigit():
        return

    approval = next(
        (item for item in approvals if item.pk == int(approval_id)),
        None,
    )
    if not approval:
        return

    label = {
        "created": "Approval aangemaakt",
        "approved": "Approval goedgekeurd",
        "rejected": "Approval afgewezen",
    }.get((event_name or "").strip())
    if not label:
        return

    run_log.append(
        {
            "label": label,
            "value": approval.get_approval_type_display(),
        }
    )


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
                "close_signal": posted_values.get("close_signal", "overdracht_klaar")
                or "overdracht_klaar",
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
        completeness_alerts = self._build_completeness_alerts(selected_thread)
        buddy_assist = build_buddy_assist_snapshot(selected_thread, completeness_alerts)

        run_log = []
        open_issues = []
        quick_actions = []

        template_query = (self.request.GET.get("template_q") or "").strip()
        template_type = (self.request.GET.get("template_type") or "").strip()
        template_tag = (self.request.GET.get("template_tag") or "").strip()
        template_id = (self.request.GET.get("template") or "").strip()
        template_action = (self.request.GET.get("template_action") or "").strip()
        templates = get_templates_for_workspace(
            "chats",
            query=template_query,
            template_type=template_type,
            tag=template_tag,
        )[:50]
        selected_template = get_template_by_id_for_workspace(template_id, "chats")

        template_context_values = {}
        if selected_thread:
            template_context_values = {
                "creator_name": selected_thread.creator.display_name,
                "channel_handle": selected_thread.channel.handle if selected_thread.channel else "",
                "platform": (
                    selected_thread.channel.get_platform_display()
                    if selected_thread.channel
                    else ""
                ),
                "next_step": selected_thread.open_loop or "",
                "last_handoff": selected_thread.last_handoff_note or "",
                "content_ready_status": (
                    selected_thread.creator.get_content_ready_status_display()
                    if selected_thread.creator.content_ready_status
                    else ""
                ),
            }

        filled_template_body = ""
        if selected_template:
            filled_template_body = _safe_template_format(
                selected_template["body"],
                template_context_values,
            )

        approvals = []
        if selected_thread:
            approvals = list(
                get_scoped_approval_queryset(self.request.user)
                .filter(thread=selected_thread)
                .order_by("-created_at", "-id")
            )

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

        if selected_template:
            run_log.append(
                {
                    "label": "Template geopend",
                    "value": selected_template["title"],
                }
            )
            if template_action == "use":
                run_log.append(
                    {
                        "label": "Template gebruikt",
                        "value": selected_template["title"],
                    }
                )

        append_approval_event(
            run_log,
            approvals,
            self.request.GET.get("approval_event"),
            self.request.GET.get("approval_id"),
        )

        return {
            "threads": threads,
            "selected_thread": selected_thread,
            "latest_draft": latest_draft,
            "completeness_alerts": completeness_alerts,
            "buddy_assist": buddy_assist,
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
            "templates": templates,
            "template_query": template_query,
            "template_type": template_type,
            "template_tag": template_tag,
            "selected_template": selected_template,
            "filled_template_body": filled_template_body,
            "template_action": template_action,
            "approvals": approvals,
            "approval_type_choices": Approval.Type.choices,
        }

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            self._build_context(thread_source="get", fallback_to_first=True)
        )

    def post(self, request, *args, **kwargs):
        posted_values = {
            "handoff_summary": (request.POST.get("handoff_summary") or "").strip(),
            "next_step": (request.POST.get("next_step") or "").strip(),
            "blocker": (request.POST.get("blocker") or "").strip(),
            "close_signal": (request.POST.get("close_signal") or "").strip()
            or "overdracht_klaar",
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
            context["submit_error"] = (
                "Handoff afsluiten is geblokkeerd: los eerst access/context issues op."
            )
            return self.render_to_response(context)

        handoff_summary = posted_values["handoff_summary"]
        next_step = posted_values["next_step"]
        blocker = posted_values["blocker"]
        close_signal = posted_values["close_signal"]

        if not handoff_summary or not next_step:
            context["submit_error"] = (
                "Laatste stand en volgende stap zijn verplicht om af te sluiten."
            )
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

        channel_with_next_step = any(
            not is_placeholder_noise(channel.session_next_action) for channel in channels
        )
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
        channels_qs = get_channel_queryset_for_user(self.request.user).select_related(
            "creator"
        )

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
        live_now_items = []
        attention_items = []
        chats_handoff_items = []
        follow_up_summary = {}
        run_log = []
        quick_actions = []

        template_query = (self.request.GET.get("template_q") or "").strip()
        template_type = (self.request.GET.get("template_type") or "").strip()
        template_tag = (self.request.GET.get("template_tag") or "").strip()
        template_id = (self.request.GET.get("template") or "").strip()
        template_action = (self.request.GET.get("template_action") or "").strip()
        templates = get_templates_for_workspace(
            "feeder",
            query=template_query,
            template_type=template_type,
            tag=template_tag,
        )[:50]

        assignment = get_active_assignment_for_user_and_creator(
            self.request.user,
            selected_creator,
        )
        relevant_handoff_channel = None

        if selected_creator:
            materials = list(
                CreatorMaterial.objects.filter(
                    creator=selected_creator,
                    active=True,
                )
                .select_related("uploaded_by")
                .order_by("-uploaded_at", "-id")[:30]
            )
            channels = list(
                channels_qs.filter(creator=selected_creator).order_by("platform", "handle")
            )
            creator_threads = list(
                get_scoped_conversation_thread_queryset(self.request.user)
                .filter(creator=selected_creator, active=True)
                .order_by("-last_message_at", "-id")[:20]
            )

            waiting_threads = [
                thread
                for thread in creator_threads
                if thread.status
                in {
                    ConversationThread.Status.WAITING_ON_OPERATOR,
                    ConversationThread.Status.HANDOFF_REQUIRED,
                }
            ]
            prioritized_threads = sorted(
                waiting_threads,
                key=lambda thread: (
                    0 if thread.status == ConversationThread.Status.HANDOFF_REQUIRED else 1,
                    0 if thread.status == ConversationThread.Status.WAITING_ON_OPERATOR else 1,
                    -(thread.last_message_at.timestamp() if thread.last_message_at else 0),
                    -thread.pk,
                ),
            )
            if waiting_threads:
                open_signals.append(
                    f"{len(waiting_threads)} thread(s) wachten op operator/handoff in Chats."
                )

            if (
                selected_creator.content_ready_status
                != selected_creator.ContentReadyStatus.READY_TO_POST
            ):
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

            if prioritized_threads:
                quick_actions.append(
                    {
                        "label": "Open Chats workspace",
                        "url": f"/chats/?thread={prioritized_threads[0].pk}",
                    }
                )
            if relevant_handoff_channel:
                quick_actions.append(
                    {
                        "label": "Open relevant channel",
                        "url": f"/channels/{relevant_handoff_channel.pk}/",
                    }
                )

            live_now_items = [
                f"Content readiness: {selected_creator.get_content_ready_status_display() or '-'}",
                f"Actief materiaal: {len(materials)} item(s)",
                (
                    f"Kanaalfocus: {relevant_handoff_channel.get_platform_display()} / "
                    f"{relevant_handoff_channel.handle}"
                    if relevant_handoff_channel
                    else "Kanaalfocus: nog niet beschikbaar"
                ),
            ]

            if (
                selected_creator.content_ready_status
                != selected_creator.ContentReadyStatus.READY_TO_POST
            ):
                attention_items.append("Content staat nog niet op ready-to-post.")
            if selected_creator.consent_status != selected_creator.ConsentStatus.ACTIVE:
                attention_items.append("Consent is niet actief; review of escalatie nodig.")
            if not selected_creator.content_source_url:
                attention_items.append("Content source ontbreekt; context aanvullen.")
            if not materials:
                attention_items.append("Geen actief materiaal beschikbaar.")

            for channel in channels:
                if not is_placeholder_noise(channel.session_blockers):
                    attention_items.append(
                        f"{channel.get_platform_display()} / {channel.handle} blocker: "
                        f"{channel.session_blockers}"
                    )
                if is_placeholder_noise(channel.session_next_action):
                    attention_items.append(
                        f"{channel.get_platform_display()} / {channel.handle}: "
                        "volgende stap ontbreekt."
                    )

            for thread in prioritized_threads:
                chats_handoff_items.append(
                    {
                        "thread_id": thread.pk,
                        "thread_ref": thread.source_thread_id,
                        "status": thread.get_status_display(),
                        "last_message_at": thread.last_message_at or "-",
                    }
                )

            follow_up_summary = {
                "pending_handoffs": sum(
                    1
                    for thread in waiting_threads
                    if thread.status == ConversationThread.Status.HANDOFF_REQUIRED
                ),
                "waiting_operator": sum(
                    1
                    for thread in waiting_threads
                    if thread.status == ConversationThread.Status.WAITING_ON_OPERATOR
                ),
                "next_chats_thread_id": prioritized_threads[0].pk if prioritized_threads else None,
                "latest_status": (
                    relevant_handoff_channel.session_updated_at
                    if relevant_handoff_channel
                    else "-"
                ),
                "next_step": (
                    relevant_handoff_channel.session_next_action
                    if relevant_handoff_channel
                    and not is_placeholder_noise(relevant_handoff_channel.session_next_action)
                    else "-"
                ),
                "work_target": (
                    f"Chats thread {prioritized_threads[0].source_thread_id}"
                    if prioritized_threads
                    else "Geen doorzet naar Chats"
                ),
            }

        approvals = []
        if selected_creator:
            approvals = list(
                get_scoped_approval_queryset(self.request.user)
                .filter(creator=selected_creator, thread__isnull=True)
                .order_by("-created_at", "-id")
            )

        selected_template = get_template_by_id_for_workspace(template_id, "feeder")
        template_context_values = {}
        if selected_creator:
            template_context_values = {
                "creator_name": selected_creator.display_name,
                "channel_handle": relevant_handoff_channel.handle if relevant_handoff_channel else "",
                "platform": (
                    relevant_handoff_channel.get_platform_display()
                    if relevant_handoff_channel
                    else ""
                ),
                "next_step": (
                    relevant_handoff_channel.session_next_action
                    if relevant_handoff_channel
                    and not is_placeholder_noise(relevant_handoff_channel.session_next_action)
                    else ""
                ),
                "last_handoff": (
                    relevant_handoff_channel.session_blockers
                    if relevant_handoff_channel
                    and not is_placeholder_noise(relevant_handoff_channel.session_blockers)
                    else ""
                ),
                "content_ready_status": (
                    selected_creator.get_content_ready_status_display()
                    if selected_creator.content_ready_status
                    else ""
                ),
            }

        filled_template_body = ""
        if selected_template:
            filled_template_body = _safe_template_format(
                selected_template["body"],
                template_context_values,
            )
            run_log.append(
                {
                    "label": "Template geopend",
                    "value": selected_template["title"],
                }
            )
            if template_action == "use":
                run_log.append(
                    {
                        "label": "Template gebruikt",
                        "value": selected_template["title"],
                    }
                )

        append_approval_event(
            run_log,
            approvals,
            self.request.GET.get("approval_event"),
            self.request.GET.get("approval_id"),
        )

        context["creators"] = creators
        context["selected_creator"] = selected_creator
        context["materials"] = materials
        context["channels"] = channels
        context["creator_threads"] = creator_threads
        context["open_signals"] = open_signals
        context["live_now_items"] = live_now_items
        context["attention_items"] = attention_items
        context["chats_handoff_items"] = chats_handoff_items
        context["follow_up_summary"] = follow_up_summary
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
        context["templates"] = templates
        context["template_query"] = template_query
        context["template_type"] = template_type
        context["template_tag"] = template_tag
        context["selected_template"] = selected_template
        context["filled_template_body"] = filled_template_body
        context["template_action"] = template_action
        context["approvals"] = approvals
        context["approval_type_choices"] = Approval.Type.choices
        return context


class ApprovalCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        workspace = (request.POST.get("workspace") or "").strip()
        approval_type = (request.POST.get("approval_type") or "").strip()
        summary = (request.POST.get("summary") or "").strip()

        if approval_type not in {choice[0] for choice in Approval.Type.choices}:
            raise Http404

        if workspace == "chats":
            thread_id = (request.POST.get("thread") or "").strip()
            if not thread_id.isdigit():
                raise Http404

            thread = get_object_or_404(
                get_scoped_conversation_thread_queryset(request.user).select_related("creator"),
                pk=int(thread_id),
            )

            creator_param = (request.POST.get("creator") or "").strip()
            if creator_param:
                if not creator_param.isdigit() or int(creator_param) != thread.creator_id:
                    raise Http404

            approval = Approval.objects.create(
                creator=thread.creator,
                thread=thread,
                approval_type=approval_type,
                summary=summary,
                requested_by=request.user,
            )
            query = urlencode(
                {
                    "thread": thread.pk,
                    "approval_event": "created",
                    "approval_id": approval.pk,
                }
            )
            return redirect(f"{reverse('chat-hub')}?{query}")

        if workspace == "feeder":
            creator_id = (request.POST.get("creator") or "").strip()
            if not creator_id.isdigit():
                raise Http404
            if (request.POST.get("thread") or "").strip():
                raise Http404

            creator = get_object_or_404(
                get_creator_queryset_for_user(request.user),
                pk=int(creator_id),
            )

            approval = Approval.objects.create(
                creator=creator,
                approval_type=approval_type,
                summary=summary,
                requested_by=request.user,
            )
            query = urlencode(
                {
                    "creator": creator.pk,
                    "approval_event": "created",
                    "approval_id": approval.pk,
                }
            )
            return redirect(f"{reverse('feeder-hub')}?{query}")

        raise Http404


class ApprovalActionBaseView(LoginRequiredMixin, View):
    event_name = ""

    def get_approval(self, request, pk):
        return get_object_or_404(get_scoped_approval_queryset(request.user), pk=pk)

    def apply_action(self, approval, user):
        raise NotImplementedError

    def post(self, request, pk, *args, **kwargs):
        approval = self.get_approval(request, pk)

        if approval.status != Approval.Status.PENDING:
            raise Http404

        try:
            self.apply_action(approval, request.user)
        except ValidationError as exc:
            raise Http404 from exc

        if approval.thread_id:
            query = urlencode(
                {
                    "thread": approval.thread_id,
                    "approval_event": self.event_name,
                    "approval_id": approval.pk,
                }
            )
            return redirect(f"{reverse('chat-hub')}?{query}")

        query = urlencode(
            {
                "creator": approval.creator_id,
                "approval_event": self.event_name,
                "approval_id": approval.pk,
            }
        )
        return redirect(f"{reverse('feeder-hub')}?{query}")


class ApprovalApproveView(ApprovalActionBaseView):
    event_name = "approved"

    def apply_action(self, approval, user):
        approval.approve(user)


class ApprovalRejectView(ApprovalActionBaseView):
    event_name = "rejected"

    def apply_action(self, approval, user):
        approval.reject(user)
