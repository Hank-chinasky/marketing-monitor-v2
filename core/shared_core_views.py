from typing import Any
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied,
    ValidationError,
)
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from core.conversation_views import get_latest_buddy_draft, get_scoped_conversation_thread_queryset
from core.models import (
    Approval,
    ConversationThread,
    CreatorMaterial,
    OperatorAssignment,
    ThreadFollowUpStatus,
)
from core.services.buddy_provider import get_configured_buddy_provider
from core.services.buddy_reply import build_operator_reply_draft
from core.services.demo_access import is_demo_viewer
from core.services.operator_context import build_operator_context
from core.services.operator_queue import build_operator_queue
from core.services.source_identity import (
    canonical_source_key,
    canonical_source_label,
    source_filter_values,
)
from core.services.scope import (
    get_active_assignments_for_operator,
    get_channel_queryset_for_user,
    get_creator_queryset_for_user,
    get_operator_for_user,
    is_admin_user,
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

CHAT_SOURCE_FILTER_OPTIONS = (
    ("", "Alle"),
    (
        ConversationThread.SourceSystem.CHATTIES,
        "Chatties",
    ),
    (
        ConversationThread.SourceSystem.EUROTIKKEN,
        "Eurotikken",
    ),
)
CHAT_SOURCE_FILTER_VALUES = {
    value
    for value, _label in CHAT_SOURCE_FILTER_OPTIONS
    if value
}


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


def _append_context_prefill_item(items, label: str, value, *, limit: int = 220) -> None:
    if is_placeholder_noise(value):
        return
    items.append({"label": label, "value": _condense_text(value, limit=limit)})


def build_buddy_assist_snapshot(
    selected_thread,
    completeness_alerts,
    follow_up_status=None,
):
    if not selected_thread:
        return {
            "status_label": "Kies gesprek",
            "why_now": "Kies een gesprek om Buddy-context te zien.",
            "thread_summary": "Nog geen actieve thread geselecteerd.",
            "profile_tone": "Geen profieltoon beschikbaar zonder thread.",
            "profile_tone_source": "Ontbreekt",
            "open_loop": "Geen actieve thread geselecteerd.",
            "do_not_do": "Start geen operatoractie zonder threadcontext.",
            "recommended_next_action": "Selecteer eerst een thread.",
            "reliability_label": "Laag",
            "reliability_badge": "badge-red",
            "reliability_reason": "Thread en broncontext ontbreken.",
            "missing_context": ["Thread ontbreekt in selectie."],
            "next_step": "Selecteer eerst een thread.",
            "session_brief": "Geen sessiebrief beschikbaar zonder thread.",
            "condensed_handoff": "",
            "has_handoff": False,
            "context_prefill": [],
        }

    missing_context = list(completeness_alerts or [])

    if is_placeholder_noise(selected_thread.thread_summary):
        missing_context.append("Threadsamenvatting ontbreekt.")
    if is_placeholder_noise(selected_thread.open_loop):
        missing_context.append("Voorgestelde volgende stap ontbreekt.")

    condensed_handoff = ""
    has_handoff = not is_placeholder_noise(selected_thread.last_handoff_note)
    if has_handoff:
        condensed_handoff = _condense_text(
            selected_thread.last_handoff_note,
            limit=220,
        )

    profile_tone = _condense_text(
        selected_thread.last_approved_reply_style,
        limit=180,
    )
    profile_tone_source = "Laatste goedgekeurde replystijl"

    profile_tone_available = bool(profile_tone)
    if not profile_tone_available:
        profile_tone = "Profieltoon ontbreekt; eerst handmatig bevestigen."
        profile_tone_source = "Ontbreekt"
        missing_context.append("Actieve profieltoon ontbreekt.")

    follow_up_why = {
        ThreadFollowUpStatus.Status.WARM: (
            "Handmatig als warm gemarkeerd; pak de opgebouwde lijn gecontroleerd op."
        ),
        ThreadFollowUpStatus.Status.OPEN_LOOP: (
            "Er staat een open loop klaar die opvolging nodig heeft."
        ),
        ThreadFollowUpStatus.Status.LATER_TRIGGEREN: (
            "Later triggeren is vastgelegd; controleer timing en context vóór actie."
        ),
        ThreadFollowUpStatus.Status.AFGEKOELD: (
            "Het gesprek is afgekoeld; forceer geen generieke heractivatie."
        ),
        ThreadFollowUpStatus.Status.REVIEW_NODIG: (
            "Operatorreview is vastgelegd voordat een vervolgstap wordt gekozen."
        ),
    }

    thread_status_labels = {
        ConversationThread.Status.ACTIVE: "Actief gesprek",
        ConversationThread.Status.WAITING_ON_OPERATOR: "Actieve follow-up",
        ConversationThread.Status.WAITING_ON_CUSTOMER: "Wacht op klant",
        ConversationThread.Status.HANDOFF_REQUIRED: "Review nodig",
        ConversationThread.Status.CLOSED: "Afgesloten",
    }

    if follow_up_status:
        status_label = follow_up_status.get_status_display()
    else:
        status_label = thread_status_labels.get(
            selected_thread.status,
            selected_thread.get_status_display(),
        )

    if selected_thread.risk_flags:
        why_now = (
            "Risicosignaal aanwezig; controleer eerst context, bron en policy."
        )
    elif follow_up_status:
        why_now = follow_up_why.get(
            follow_up_status.status,
            "Handmatige follow-upstatus vraagt operatoraandacht.",
        )
    elif selected_thread.status == ConversationThread.Status.WAITING_ON_OPERATOR:
        if not is_placeholder_noise(selected_thread.open_loop):
            why_now = (
                "De klant wacht op operatoropvolging en er staat een concrete "
                "open loop klaar."
            )
        else:
            why_now = (
                "De klant wacht op operatoropvolging; leg eerst een concrete "
                "vervolgstap vast."
            )
    elif selected_thread.status == ConversationThread.Status.WAITING_ON_CUSTOMER:
        why_now = (
            "De operatorlijn staat; wacht op klant en vermijd onnodig opnieuw benaderen."
        )
    elif selected_thread.status == ConversationThread.Status.HANDOFF_REQUIRED:
        why_now = (
            "De thread vraagt overdracht of review voordat de lijn wordt voortgezet."
        )
    elif selected_thread.status == ConversationThread.Status.CLOSED:
        why_now = (
            "De thread is gesloten; alleen heropenen met een expliciete reden."
        )
    elif not is_placeholder_noise(selected_thread.open_loop):
        why_now = "Er staat een concrete vervolgstap klaar voor operatorreview."
    else:
        why_now = "Lees de context en bepaal handmatig of opvolging nodig is."

    do_not_do_parts = []

    if selected_thread.risk_flags:
        do_not_do_parts.append(
            "Niet handelen voordat risicosignalen handmatig zijn beoordeeld."
        )

    if not profile_tone_available:
        do_not_do_parts.append(
            "Niet generiek openen of een profieltoon verzinnen."
        )

    if not is_placeholder_noise(selected_thread.guardrails):
        do_not_do_parts.append(
            f"Guardrail: {_condense_text(selected_thread.guardrails, limit=180)}"
        )

    if not do_not_do_parts:
        do_not_do_parts.append(
            "Niet automatisch verzenden en de bestaande gesprekstrant niet resetten."
        )

    do_not_do = " ".join(do_not_do_parts)

    open_loop = (
        _condense_text(selected_thread.open_loop, limit=220)
        or "Geen concrete open loop vastgelegd."
    )

    if selected_thread.risk_flags:
        recommended_next_action = (
            "Beoordeel eerst het risicosignaal en bevestig de betrouwbare context."
        )
    elif not is_placeholder_noise(selected_thread.open_loop):
        recommended_next_action = _condense_text(
            selected_thread.open_loop,
            limit=220,
        )
    elif missing_context:
        recommended_next_action = f"Vul eerst aan: {missing_context[0]}"
    else:
        recommended_next_action = (
            "Lees de laatste berichten en leg een concrete vervolgstap vast."
        )

    missing_context = list(dict.fromkeys(missing_context))

    if (
        selected_thread.risk_flags
        or not selected_thread.channel
        or len(missing_context) >= 3
    ):
        reliability_label = "Laag"
        reliability_badge = "badge-red"
        reliability_reason = (
            "Risico, ontbrekende bron of meerdere essentiële contextgaten."
        )
    elif missing_context:
        reliability_label = "Middel"
        reliability_badge = "badge-yellow"
        reliability_reason = (
            "Bruikbare context aanwezig, maar menselijke aanvulling blijft nodig."
        )
    else:
        reliability_label = "Hoog"
        reliability_badge = "badge-green"
        reliability_reason = (
            "Kerncontext, bron en profieltoon zijn aanwezig."
        )

    context_prefill = []
    _append_context_prefill_item(
        context_prefill,
        "Creator",
        selected_thread.creator.display_name,
    )
    _append_context_prefill_item(
        context_prefill,
        "Customer stage",
        selected_thread.creator.get_customer_stage_display(),
    )

    if selected_thread.channel:
        channel = selected_thread.channel
        _append_context_prefill_item(
            context_prefill,
            "Channel",
            f"{channel.get_platform_display()} / {channel.handle}",
        )
        _append_context_prefill_item(
            context_prefill,
            "Profile URL",
            channel.profile_url,
        )
        _append_context_prefill_item(
            context_prefill,
            "Access notes",
            channel.access_profile_notes or channel.access_notes,
        )

    _append_context_prefill_item(
        context_prefill,
        "Guardrails",
        selected_thread.guardrails,
    )

    session_brief_parts = [
        f"Status: {selected_thread.get_status_display()}",
        f"Bron: {canonical_source_label(selected_thread.source_system)}",
        (
            f"Laatste operator-handoff: {selected_thread.last_operator_handoff_at}"
            if selected_thread.last_operator_handoff_at
            else "Laatste operator-handoff: -"
        ),
    ]

    return {
        "status_label": status_label,
        "why_now": why_now,
        "thread_summary": (
            _condense_text(selected_thread.thread_summary, limit=220)
            or "Nog geen threadsamenvatting beschikbaar."
        ),
        "profile_tone": profile_tone,
        "profile_tone_source": profile_tone_source,
        "open_loop": open_loop,
        "do_not_do": do_not_do,
        "recommended_next_action": recommended_next_action,
        "reliability_label": reliability_label,
        "reliability_badge": reliability_badge,
        "reliability_reason": reliability_reason,
        "missing_context": missing_context,
        "next_step": open_loop,
        "session_brief": " · ".join(session_brief_parts),
        "condensed_handoff": condensed_handoff,
        "has_handoff": has_handoff,
        "context_prefill": context_prefill,
    }


def build_feeder_buddy_assist_snapshot(
    selected_creator,
    relevant_handoff_channel,
    follow_up_summary,
    completeness_alerts,
):
    if not selected_creator:
        return {
            "creator_summary": "Geen creator geselecteerd.",
            "missing_context": ["Creator ontbreekt in selectie."],
            "next_step": "Selecteer eerst een creator.",
            "session_brief": "Geen sessiebrief beschikbaar zonder creator.",
            "condensed_handoff": "",
            "has_handoff": False,
            "context_prefill": [],
        }

    missing_context = list(completeness_alerts or [])
    if not relevant_handoff_channel:
        missing_context.append("Kanaalhandoff ontbreekt.")

    if (
        follow_up_summary
        and follow_up_summary.get("next_chats_thread_id")
        and not is_placeholder_noise(follow_up_summary.get("work_target"))
    ):
        next_step = f"Zet door naar {follow_up_summary['work_target']}."
    elif relevant_handoff_channel and not is_placeholder_noise(
        relevant_handoff_channel.session_next_action
    ):
        next_step = _condense_text(relevant_handoff_channel.session_next_action, limit=220)
    else:
        next_step = "Nog geen concrete volgende stap vastgelegd."

    handoff_text = ""
    if relevant_handoff_channel and not is_placeholder_noise(
        relevant_handoff_channel.session_blockers
    ):
        handoff_text = relevant_handoff_channel.session_blockers
    elif relevant_handoff_channel and not is_placeholder_noise(
        relevant_handoff_channel.session_next_action
    ):
        handoff_text = relevant_handoff_channel.session_next_action

    condensed_handoff = _condense_text(handoff_text, limit=220)
    has_handoff = bool(condensed_handoff)

    context_prefill = []
    _append_context_prefill_item(context_prefill, "Creator", selected_creator.display_name)
    _append_context_prefill_item(
        context_prefill,
        "Customer stage",
        selected_creator.get_customer_stage_display(),
    )
    _append_context_prefill_item(
        context_prefill,
        "Content status",
        selected_creator.get_content_ready_status_display(),
    )
    _append_context_prefill_item(
        context_prefill,
        "Content source",
        selected_creator.content_source_url,
    )
    if relevant_handoff_channel:
        _append_context_prefill_item(
            context_prefill,
            "Channel",
            (
                f"{relevant_handoff_channel.get_platform_display()} / "
                f"{relevant_handoff_channel.handle}"
            ),
        )
        _append_context_prefill_item(
            context_prefill,
            "Profile URL",
            relevant_handoff_channel.profile_url,
        )
        _append_context_prefill_item(
            context_prefill,
            "Access notes",
            relevant_handoff_channel.access_profile_notes
            or relevant_handoff_channel.access_notes,
        )

    session_brief_parts = [
        (
            f"Creator: {selected_creator.display_name}"
            if selected_creator.display_name
            else "Creator: -"
        ),
        (
            "Content status: "
            f"{selected_creator.get_content_ready_status_display() or '-'}"
        ),
        (
            f"Laatste feeder handoff: {relevant_handoff_channel.session_updated_at}"
            if relevant_handoff_channel and relevant_handoff_channel.session_updated_at
            else "Laatste feeder handoff: -"
        ),
    ]

    return {
        "creator_summary": (
            f"{selected_creator.display_name} · "
            f"{selected_creator.get_content_ready_status_display() or 'status onbekend'}"
        ),
        "missing_context": missing_context,
        "next_step": next_step,
        "session_brief": " · ".join(session_brief_parts),
        "condensed_handoff": condensed_handoff,
        "has_handoff": has_handoff,
        "context_prefill": context_prefill,
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

        if (
            selected_thread.source_system
            == ConversationThread.SourceSystem.EUROTIKKEN
        ):
            try:
                selected_thread.context_snapshot
            except ObjectDoesNotExist:
                alerts.append("Bronprofielcontext ontbreekt.")

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

        if is_demo_viewer(self.request.user):
            return {
                "status": "readonly",
                "label": "read-only demo",
                "badge": "badge-blue",
                "reason": (
                    "Demoweergave: bekijken is toegestaan; "
                    "alle wijzigingen zijn geblokkeerd."
                ),
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

    def _get_source_filter(self, *, source="get"):
        request_values = (
            self.request.POST
            if source == "post"
            else self.request.GET
        )
        source_filter = (
            request_values.get("source") or ""
        ).strip().lower()

        if source_filter not in CHAT_SOURCE_FILTER_VALUES:
            return ""

        return source_filter

    def _get_focus_mode(self, *, source="get"):
        request_values = (
            self.request.POST
            if source == "post"
            else self.request.GET
        )
        return request_values.get("focus") == "1"

    def _get_threads(self, source_filter=""):
        queryset = (
            get_scoped_conversation_thread_queryset(
                self.request.user
            )
            .select_related(
                "creator",
                "channel",
                "follow_up_status",
                "context_snapshot",
            )
        )

        if source_filter:
            queryset = queryset.filter(
                source_system__in=source_filter_values(
                    source_filter
                )
            )

        return list(
            queryset.order_by(
                "-last_message_at",
                "-id",
            )
        )

    def _resolve_selected_thread(
        self,
        threads,
        *,
        source="get",
        fallback_to_first=True,
        fallback_on_invalid=True,
    ):
        selected_thread = None
        selected_thread_param = ""

        if source == "post":
            selected_thread_param = (self.request.POST.get("thread") or "").strip()
        else:
            selected_thread_param = (self.request.GET.get("thread") or "").strip()

        if selected_thread_param.isdigit():
            selected_thread = next(
                (
                    thread
                    for thread in threads
                    if thread.pk == int(selected_thread_param)
                ),
                None,
            )

        if (
            selected_thread_param
            and selected_thread is None
            and not fallback_on_invalid
        ):
            return None

        if (
            selected_thread is None
            and fallback_to_first
            and threads
        ):
            selected_thread = threads[0]

        return selected_thread

    @staticmethod
    def _apply_follow_up_completion_status(selected_thread, follow_up_value):
        target_status = {
            ThreadFollowUpStatus.Status.WARM: (
                ConversationThread.Status.WAITING_ON_CUSTOMER
            ),
            ThreadFollowUpStatus.Status.OPEN_LOOP: (
                ConversationThread.Status.WAITING_ON_CUSTOMER
            ),
            ThreadFollowUpStatus.Status.REVIEW_NODIG: (
                ConversationThread.Status.HANDOFF_REQUIRED
            ),
        }.get(follow_up_value)

        if target_status and selected_thread.status != target_status:
            selected_thread.status = target_status
            selected_thread.save(update_fields=["status"])

    @staticmethod
    def _get_handoff_completion_status(close_signal):
        return {
            "overdracht_klaar": ConversationThread.Status.WAITING_ON_CUSTOMER,
            "review_nodig": ConversationThread.Status.HANDOFF_REQUIRED,
            "opvolging_nodig": ConversationThread.Status.WAITING_ON_OPERATOR,
        }.get(close_signal)

    def _build_source_filter_options(
        self,
        selected_thread,
        *,
        source_filter,
        focus_mode,
    ):
        options = []

        for value, label in CHAT_SOURCE_FILTER_OPTIONS:
            query_values = {}

            if value:
                query_values["source"] = value

            if (
                selected_thread
                and (
                    not value
                    or canonical_source_key(
                        selected_thread.source_system
                    ) == value
                )
            ):
                query_values["thread"] = selected_thread.pk

            if focus_mode:
                query_values["focus"] = 1

            query = urlencode(query_values)
            url = reverse("chat-hub")
            if query:
                url = f"{url}?{query}"

            options.append(
                {
                    "value": value,
                    "label": label,
                    "active": source_filter == value,
                    "url": url,
                }
            )

        return options

    def _redirect_after_queue_completion(
        self,
        selected_thread,
        *,
        completion_kind,
    ):
        source_filter = self._get_source_filter(
            source="post"
        )
        refreshed_threads = self._get_threads(
            source_filter
        )
        operator_queue = build_operator_queue(
            refreshed_threads
        )

        next_item = next(
            (
                item
                for item in operator_queue["active_items"]
                if item["thread"].pk != selected_thread.pk
            ),
            None,
        )

        query_values = {
            "queue_saved": completion_kind,
        }

        if next_item:
            query_values["thread"] = next_item["thread"].pk
            query_values["queue_advanced"] = 1
        else:
            query_values["thread"] = selected_thread.pk
            query_values["queue_cycle_complete"] = 1

        if source_filter:
            query_values["source"] = source_filter

        if self.request.POST.get("focus") == "1":
            query_values["focus"] = 1

        query = urlencode(query_values)
        return redirect(f"{reverse('chat-hub')}?{query}")

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


    def _build_chat_scan_context(self, selected_thread):
        if not selected_thread:
            return {
                "chat_focus_items": [],
                "latest_handoff_scan": {
                    "summary": "Geen actieve handoff beschikbaar zonder thread.",
                    "at": "-",
                },
                "next_step_scan": "Nog geen volgende stap beschikbaar zonder thread.",
            }

        chat_focus_items = [
            {
                "label": "Creator",
                "value": selected_thread.creator.display_name or "-",
            },
            {
                "label": "Thread",
                "value": selected_thread.source_thread_id or "-",
            },
            {
                "label": "Threadsamenvatting",
                "value": _condense_text(selected_thread.thread_summary, limit=220)
                or "Nog geen threadsamenvatting vastgelegd.",
            },
            {
                "label": "Laatste statusmoment",
                "value": (
                    f"{selected_thread.get_status_display()} · "
                    f"{selected_thread.last_message_at or '-'}"
                ),
            },
        ]

        latest_handoff_scan = {
            "summary": _condense_text(selected_thread.last_handoff_note, limit=260)
            or "Nog geen handoff-note beschikbaar.",
            "at": selected_thread.last_operator_handoff_at or "-",
        }
        next_step_scan = _condense_text(selected_thread.open_loop, limit=260) or (
            "Los eerst op: Volgende stap ontbreekt (open loop leeg)."
        )

        return {
            "chat_focus_items": chat_focus_items,
            "latest_handoff_scan": latest_handoff_scan,
            "next_step_scan": next_step_scan,
        }

    def _build_context(
        self,
        *,
        submit_error="",
        handoff_form_data=None,
        thread_source="get",
        fallback_to_first=True,
    ):
        demo_read_only = is_demo_viewer(
            self.request.user
        )
        source_filter = self._get_source_filter(
            source=thread_source
        )
        focus_mode = self._get_focus_mode(
            source=thread_source
        )
        threads = self._get_threads(source_filter)
        operator_queue = build_operator_queue(threads)
        selected_thread = self._resolve_selected_thread(
            threads,
            source=thread_source,
            fallback_to_first=fallback_to_first,
            fallback_on_invalid=not bool(source_filter),
        )

        request_values = (
            self.request.POST
            if thread_source == "post"
            else self.request.GET
        )
        selected_thread_param = (
            request_values.get("thread") or ""
        ).strip()
        source_filter_thread_mismatch = bool(
            source_filter
            and selected_thread_param
            and selected_thread is None
        )
        source_filter_options = (
            self._build_source_filter_options(
                selected_thread,
                source_filter=source_filter,
                focus_mode=focus_mode,
            )
        )
        source_filter_label = dict(
            CHAT_SOURCE_FILTER_OPTIONS
        )[source_filter]

        assignment = get_active_assignment_for_user_and_creator(
            self.request.user,
            selected_thread.creator if selected_thread else None,
        )
        assignment_context = build_assignment_context(assignment)
        if demo_read_only:
            assignment_context = {
                "has_active_assignment": False,
                "status_label": "demo viewer",
                "scope_label": "Read-only",
            }

        access_state = self._build_access_state(selected_thread, assignment)
        latest_draft = get_latest_buddy_draft(selected_thread) if selected_thread else None
        completeness_alerts = self._build_completeness_alerts(selected_thread)
        operator_context = build_operator_context(selected_thread)

        follow_up_status = None
        if selected_thread:
            follow_up_status = ThreadFollowUpStatus.objects.filter(
                thread=selected_thread,
            ).first()

        buddy_assist = build_buddy_assist_snapshot(
            selected_thread,
            completeness_alerts,
            follow_up_status=follow_up_status,
        )

        if operator_context["available"]:
            buddy_assist["profile_context"] = dict(
                operator_context["profile"]
            )
            buddy_assist["customer_context"] = dict(
                operator_context["customer"]
            )

        if operator_context["customer_review_missing"]:
            buddy_assist["reliability_label"] = "Laag"
            buddy_assist["reliability_badge"] = "badge-red"
            buddy_assist["reliability_reason"] = (
                "Klantcontext is nog niet gereviewd."
            )
        elif (
            operator_context["customer_reliability_warning"]
            and buddy_assist["reliability_label"] != "Laag"
        ):
            buddy_assist["reliability_label"] = "Middel"
            buddy_assist["reliability_badge"] = "badge-yellow"
            buddy_assist["reliability_reason"] = (
                "Klantcontext is gereviewd, maar niet aan de "
                "bron gecontroleerd."
            )

        chat_scan_context = self._build_chat_scan_context(selected_thread)
        conversation_messages = []
        if selected_thread:
            conversation_messages = list(
                selected_thread.conversation_messages.order_by("occurred_at", "id")
            )
        conversation_messages = list(conversation_messages)
        conversation_message_count = len(conversation_messages)
        conversation_history_expanded = (
            self.request.GET.get("history") == "all"
        )

        if (
            not conversation_history_expanded
            and conversation_message_count > 5
        ):
            conversation_messages = conversation_messages[-5:]

        conversation_hidden_message_count = max(
            0,
            conversation_message_count - len(conversation_messages),
        )

        operator_reply_draft = build_operator_reply_draft(
            selected_thread,
            conversation_messages,
            latest_draft=latest_draft,
            operator=get_operator_for_user(self.request.user),
            buddy_context=buddy_assist,
            provider=get_configured_buddy_provider(),
        )

        run_log = []
        open_issues = []
        quick_actions = []
        can_create_conversation_thread = (
            not demo_read_only
            and (
                is_admin_user(self.request.user)
                or get_creator_queryset_for_user(self.request.user).exists()
            )
        )

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

        follow_up_form = {
            "status": follow_up_status.status if follow_up_status else "",
            "note": follow_up_status.note if follow_up_status else "",
        }

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
            if access_state["status"] == "review_needed":
                open_issues.extend(
                    [
                        item
                        for item in completeness_alerts
                        if item not in open_issues
                    ]
                )

            quick_actions.append(
                {
                    "label": "Open thread detail",
                    "url": f"/conversations/{selected_thread.pk}/",
                }
            )
            if (
                not demo_read_only
                and latest_draft
                and latest_draft.state == latest_draft.State.DRAFTED
            ):
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
            "operator_queue": operator_queue,
            "selected_thread": selected_thread,
            "source_filter": source_filter,
            "source_filter_label": source_filter_label,
            "source_filter_options": source_filter_options,
            "source_filter_active": bool(source_filter),
            "source_filter_empty": bool(
                source_filter and not threads
            ),
            "source_filter_thread_mismatch": (
                source_filter_thread_mismatch
            ),
            "conversation_messages": conversation_messages,
            "conversation_message_count": conversation_message_count,
            "conversation_hidden_message_count": (
                conversation_hidden_message_count
            ),
            "conversation_history_expanded": (
                conversation_history_expanded
            ),
            "operator_reply_draft": operator_reply_draft,
            "latest_draft": latest_draft,
            "completeness_alerts": completeness_alerts,
            "operator_context": operator_context,
            "buddy_assist": buddy_assist,
            "chat_focus_items": chat_scan_context["chat_focus_items"],
            "latest_handoff_scan": chat_scan_context["latest_handoff_scan"],
            "next_step_scan": chat_scan_context["next_step_scan"],
            "assignment_context": assignment_context,
            "access_state": access_state,
            "demo_read_only": demo_read_only,
            "run_log": run_log,
            "open_issues": open_issues,
            "quick_actions": quick_actions,
            "can_create_conversation_thread": can_create_conversation_thread,
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
            "follow_up_status": follow_up_status,
            "follow_up_status_choices": ThreadFollowUpStatus.Status.choices,
            "follow_up_form": follow_up_form,
            "follow_up_saved": self.request.GET.get("follow_up_saved") == "1",
            "follow_up_submit_error": None,
            "focus_mode": focus_mode,
            "queue_saved": (
                self.request.GET.get("queue_saved")
                if self.request.GET.get("queue_saved")
                in {"follow_up", "handoff"}
                else ""
            ),
            "queue_advanced": self.request.GET.get("queue_advanced") == "1",
            "queue_cycle_complete": (
                self.request.GET.get("queue_cycle_complete") == "1"
            ),
        }

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            self._build_context(thread_source="get", fallback_to_first=True)
        )

    def post(self, request, *args, **kwargs):
        if is_demo_viewer(request.user):
            raise PermissionDenied("Demo viewer access is read-only.")

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
            if request.POST.get("form_action") == "follow_up_status":
                context["follow_up_submit_error"] = (
                    "Geen actieve thread geselecteerd voor follow-up status."
                )
            else:
                context["submit_error"] = "Geen actieve thread geselecteerd voor handoff-afsluiting."
            return self.render_to_response(context)

        if request.POST.get("form_action") == "follow_up_status":
            follow_up_value = (request.POST.get("follow_up_status") or "").strip()
            follow_up_note = (request.POST.get("follow_up_note") or "").strip()
            allowed_statuses = {choice[0] for choice in ThreadFollowUpStatus.Status.choices}

            context["follow_up_form"] = {
                "status": follow_up_value,
                "note": follow_up_note,
            }

            if follow_up_value not in allowed_statuses:
                context["follow_up_submit_error"] = "Kies een geldige follow-up status."
                return self.render_to_response(context)

            follow_up_status, created = ThreadFollowUpStatus.objects.get_or_create(
                thread=selected_thread,
                defaults={
                    "status": follow_up_value,
                    "note": follow_up_note,
                    "created_by": request.user,
                    "updated_by": request.user,
                },
            )

            if not created:
                follow_up_status.status = follow_up_value
                follow_up_status.note = follow_up_note
                follow_up_status.updated_by = request.user
                follow_up_status.save(
                    update_fields=[
                        "status",
                        "note",
                        "updated_by",
                        "updated_at",
                    ]
                )

            if request.POST.get("queue_action") == "save_and_next":
                self._apply_follow_up_completion_status(
                    selected_thread,
                    follow_up_value,
                )
                return self._redirect_after_queue_completion(
                    selected_thread,
                    completion_kind="follow_up",
                )

            query_values = {
                "thread": selected_thread.pk,
                "follow_up_saved": 1,
            }
            source_filter = self._get_source_filter(
                source="post"
            )
            if source_filter:
                query_values["source"] = source_filter
            if request.POST.get("focus") == "1":
                query_values["focus"] = "1"
            query = urlencode(query_values)
            return redirect(f"{reverse('chat-hub')}?{query}")

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

        update_fields = [
            "last_handoff_note",
            "open_loop",
            "last_operator_handoff_at",
        ]

        if request.POST.get("queue_action") == "save_and_next":
            completion_status = self._get_handoff_completion_status(
                close_signal
            )
            if completion_status and selected_thread.status != completion_status:
                selected_thread.status = completion_status
                update_fields.append("status")

        selected_thread.save(update_fields=update_fields)

        if request.POST.get("queue_action") == "save_and_next":
            return self._redirect_after_queue_completion(
                selected_thread,
                completion_kind="handoff",
            )

        query_values = {
            "thread": selected_thread.pk,
            "saved": 1,
        }
        source_filter = self._get_source_filter(
            source="post"
        )
        if source_filter:
            query_values["source"] = source_filter
        if request.POST.get("focus") == "1":
            query_values["focus"] = "1"
        query = urlencode(query_values)
        return redirect(f"{reverse('chat-hub')}?{query}")


class ProfileContentView(LoginRequiredMixin, TemplateView):
    """Read-only source-aware profile content surface."""

    template_name = "chats/profile_content.html"
    http_method_names = ["get", "head", "options"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        thread = get_object_or_404(
            get_scoped_conversation_thread_queryset(
                self.request.user
            ),
            pk=kwargs["thread_pk"],
        )
        operator_context = build_operator_context(thread)

        if not operator_context["available"]:
            raise Http404(
                "Profile context is unavailable."
            )

        return_query = {"thread": thread.pk}
        focus_mode = self.request.GET.get("focus") == "1"
        if focus_mode:
            return_query["focus"] = 1

        source_filter = (
            self.request.GET.get("source") or ""
        ).strip().lower()
        if source_filter not in CHAT_SOURCE_FILTER_VALUES:
            source_filter = ""
        if source_filter:
            return_query["source"] = source_filter

        context.update(
            {
                "thread": thread,
                "operator_context": operator_context,
                "profile_media": operator_context[
                    "profile_media"
                ],
                "profile_media_count": len(
                    operator_context["profile_media"]
                ),
                "focus_mode": focus_mode,
                "source_filter": source_filter,
                "return_url": (
                    f"{reverse('chat-hub')}?"
                    f"{urlencode(return_query)}"
                ),
            }
        )

        return context


class FeederHubView(LoginRequiredMixin, TemplateView):
    template_name = "feeder/feeder_hub.html"

    def _build_context(
        self,
        *,
        selected_creator,
        relevant_handoff_channel,
        follow_up_summary,
        completeness_alerts,
    ):
        buddy_assist = build_feeder_buddy_assist_snapshot(
            selected_creator,
            relevant_handoff_channel,
            follow_up_summary,
            completeness_alerts,
        )
        return {"buddy_assist": buddy_assist}

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

    def _build_feeder_scan_context(
        self,
        *,
        live_now_items,
        attention_items,
        chats_handoff_items,
        follow_up_summary,
        run_log,
        relevant_handoff_channel,
        completeness_alerts,
        access_state,
    ):
        feeder_focus_items = [
            {"label": "Access", "value": access_state.get("label", "-")},
            {
                "label": "Live focus",
                "value": live_now_items[0] if live_now_items else "Geen live focus beschikbaar.",
            },
            {
                "label": "Aandacht",
                "value": attention_items[0] if attention_items else "Geen extra aandachtspunten.",
            },
        ]

        latest_feeder_handoff_scan = {
            "channel": (
                f"{relevant_handoff_channel.get_platform_display()} / {relevant_handoff_channel.handle}"
                if relevant_handoff_channel
                else "Geen channel handoff-context binnen scope."
            ),
            "status": follow_up_summary.get("latest_status", "-"),
            "blocker": (
                relevant_handoff_channel.session_blockers
                if relevant_handoff_channel
                and not is_placeholder_noise(relevant_handoff_channel.session_blockers)
                else "-"
            ),
        }

        next_operator_action_scan = follow_up_summary.get("next_step") or "-"
        if next_operator_action_scan == "-":
            if completeness_alerts:
                next_operator_action_scan = f"Los eerst op: {completeness_alerts[0]}"
            elif run_log:
                next_operator_action_scan = f"Scan {run_log[-1]['label']}."
            else:
                next_operator_action_scan = "Geen volgende operatoractie beschikbaar."

        chats_handoff_scan = {
            "count": len(chats_handoff_items),
            "target": follow_up_summary.get("work_target") or "Geen doorzet naar Chats",
        }

        return {
            "feeder_focus_items": feeder_focus_items,
            "latest_feeder_handoff_scan": latest_feeder_handoff_scan,
            "next_operator_action_scan": next_operator_action_scan,
            "chats_handoff_scan": chats_handoff_scan,
        }

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
        context.update(
            self._build_feeder_scan_context(
                live_now_items=live_now_items,
                attention_items=attention_items,
                chats_handoff_items=chats_handoff_items,
                follow_up_summary=follow_up_summary,
                run_log=run_log,
                relevant_handoff_channel=relevant_handoff_channel,
                completeness_alerts=context["completeness_alerts"],
                access_state=context["access_state"],
            )
        )
        context.update(
            self._build_context(
                selected_creator=selected_creator,
                relevant_handoff_channel=relevant_handoff_channel,
                follow_up_summary=follow_up_summary,
                completeness_alerts=context["completeness_alerts"],
            )
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
        if is_demo_viewer(request.user):
            raise PermissionDenied("Demo viewer access is read-only.")

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
        if is_demo_viewer(request.user):
            raise PermissionDenied("Demo viewer access is read-only.")

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