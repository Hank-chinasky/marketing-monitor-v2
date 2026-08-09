from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from core.services.buddy_context import build_buddy_context_packet
from core.services.buddy_output import (
    BuddyOutputValidationError,
    validate_buddy_output,
)


class BuddyReplyProvider(Protocol):
    """Provider-independent contract for future Buddy reply providers."""

    def generate_reply(
        self,
        *,
        context_packet: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Return structured output for one controlled context packet."""


@dataclass(frozen=True)
class OperatorReplyDraft:
    status: str
    status_label: str
    status_badge: str
    latest_inbound_text: str
    reply_text: str
    language: str
    source: str
    provider_error: str
    requires_human_review: bool
    safety_note: str
    missing_context_note: str
    tone_note: str


_REPLY_STATUS_META = {
    "no_thread": ("No conversation", "badge-yellow"),
    "no_inbound_message": ("No customer message", "badge-yellow"),
    "existing_draft": ("Existing Buddy draft", "badge-blue"),
    "provider_unavailable": ("No Buddy reply yet", "badge-yellow"),
    "provider_error": ("Provider error", "badge-red"),
    "provider_refusal": ("Buddy did not provide a draft", "badge-yellow"),
    "ready": ("Draft ready", "badge-green"),
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _message_direction(message: Any) -> str:
    return _text(getattr(message, "direction", ""))


def _message_body(message: Any) -> str:
    return _text(getattr(message, "body", ""))


def _latest_inbound_body(conversation_messages: Iterable[Any]) -> str:
    messages = list(conversation_messages or [])

    for message in reversed(messages):
        if _message_direction(message) == "inbound":
            body = _message_body(message)
            if body:
                return body

    return ""


def _marker_score(text: str, markers: set[str]) -> int:
    return sum(1 for marker in markers if marker in text)


def _detect_language(text: str) -> str:
    lowered = _text(text).lower()

    if not lowered:
        return "unknown"

    scores = {
        "pt": _marker_score(
            lowered,
            {
                "olá",
                "ola",
                "obrigado",
                "obrigada",
                "tudo bem",
                "por favor",
                "mensagem",
                "resposta",
                "vocês",
                "voces",
            },
        ),
        "nl": _marker_score(
            lowered,
            {
                "hoi",
                "hallo",
                "dank",
                "dankjewel",
                "bericht",
                "graag",
                "kun je",
                "kunt u",
                "wanneer",
                "morgen",
                "helpen",
            },
        ),
        "de": _marker_score(
            lowered,
            {
                "hallo",
                "danke",
                "bitte",
                "nachricht",
                "antwort",
                "kannst du",
                "können sie",
                "heute",
                "morgen",
                "frage",
                "beantworten",
            },
        ),
        "en": _marker_score(
            lowered,
            {
                "hello",
                "hi",
                "thanks",
                "thank you",
                "message",
                "reply",
                "can you",
                "could you",
                "today",
                "tomorrow",
                "question",
                "help",
            },
        ),
    }

    best_language, best_score = max(scores.items(), key=lambda item: item[1])

    if best_score > 0:
        return best_language

    return "unknown"


def _draft(
    *,
    status: str,
    latest_inbound_text: str,
    reply_text: str,
    language: str,
    source: str,
    safety_note: str,
    provider_error: str = "",
    missing_context_note: str = "",
    tone_note: str = "",
) -> dict[str, Any]:
    status_label, status_badge = _REPLY_STATUS_META[status]

    return asdict(
        OperatorReplyDraft(
            status=status,
            status_label=status_label,
            status_badge=status_badge,
            latest_inbound_text=latest_inbound_text,
            reply_text=reply_text,
            language=language,
            source=source,
            provider_error=provider_error,
            requires_human_review=True,
            safety_note=safety_note,
            missing_context_note=missing_context_note,
            tone_note=tone_note,
        )
    )


def _provider_error_draft(
    *,
    latest_inbound_text: str,
    language: str,
    source: str,
) -> dict[str, Any]:
    return _draft(
        status="provider_error",
        latest_inbound_text=latest_inbound_text,
        reply_text="",
        language=language,
        source=source,
        provider_error=(
            "The Buddy provider could not produce a valid draft. "
            "No automatic or generic reply was inserted."
        ),
        safety_note=(
            "No provider output is available. "
            "The operator must decide whether a manual reply is safe."
        ),
        tone_note="Check provider status and context before continuing.",
    )


def _provider_refusal_draft(
    *,
    latest_inbound_text: str,
    language: str,
    source: str,
    reason: str,
) -> dict[str, Any]:
    return _draft(
        status="provider_refusal",
        latest_inbound_text=latest_inbound_text,
        reply_text="",
        language=language,
        source=source,
        safety_note=(
            "Buddy deliberately did not provide a reply draft. "
            "The operator must review the visible context."
        ),
        missing_context_note=(
            "No safe provider draft is available."
        ),
        tone_note=reason or (
            "Review the conversation manually before replying."
        ),
    )


def build_operator_reply_draft(
    selected_thread,
    conversation_messages,
    *,
    latest_draft=None,
    operator=None,
    buddy_context: Mapping[str, Any] | None = None,
    provider: BuddyReplyProvider | None = None,
) -> dict[str, Any]:
    """Build a read-only reply-workspace snapshot.

    This boundary never creates BuddyDraft rows, changes thread state, calls a
    source platform or sends a message. When no provider is supplied, it exposes
    an explicit unavailable state instead of presenting canned text as AI output.
    """

    messages = list(conversation_messages or [])

    if not selected_thread:
        return _draft(
            status="no_thread",
            latest_inbound_text="",
            reply_text="",
            language="unknown",
            source="no_thread",
            safety_note=(
                "No active thread selected. "
                "No reply may be used."
            ),
            missing_context_note="No active thread selected.",
            tone_note="Select a conversation first.",
        )

    latest_inbound_text = _latest_inbound_body(messages)
    language = _detect_language(latest_inbound_text)

    if not latest_inbound_text:
        return _draft(
            status="no_inbound_message",
            latest_inbound_text="",
            reply_text="",
            language="unknown",
            source="no_inbound_message",
            safety_note=(
                "No inbound customer message is available. "
                "No reply may be used."
            ),
            missing_context_note="No inbound customer message is available.",
            tone_note="Wait for customer context before drafting a reply.",
        )

    existing_reply_text = _text(getattr(latest_draft, "reply_text", ""))

    if existing_reply_text:
        return _draft(
            status="existing_draft",
            latest_inbound_text=latest_inbound_text,
            reply_text=existing_reply_text,
            language=language,
            source="latest_buddy_draft",
            safety_note=(
                "Draft only. The operator must check the existing Buddy draft "
                "against the visible messages and context."
            ),
            tone_note=(
                "Check whether the existing draft correctly follows the latest customer message, "
                "profile tone and open loop."
            ),
        )

    if provider is None:
        return _draft(
            status="provider_unavailable",
            latest_inbound_text=latest_inbound_text,
            reply_text="",
            language=language,
            source="provider_unavailable",
            safety_note=(
                "No Buddy provider is connected. "
                "A manually entered draft is not AI output."
            ),
            tone_note=(
                "The operator can type a draft manually, but Buddy has not "
                "generated a reply in this state."
            ),
        )

    provider_name = provider.__class__.__name__

    context_packet = build_buddy_context_packet(
        selected_thread,
        messages,
        buddy_assist=buddy_context,
        language=language,
    )

    try:
        provider_result = provider.generate_reply(
            context_packet=context_packet,
        )
    except Exception:
        return _provider_error_draft(
            latest_inbound_text=latest_inbound_text,
            language=language,
            source=f"provider_error:{provider_name}",
        )

    try:
        validated_output = validate_buddy_output(
            provider_result,
        )
    except BuddyOutputValidationError:
        return _provider_error_draft(
            latest_inbound_text=latest_inbound_text,
            language=language,
            source=f"provider_error:{provider_name}",
        )

    provider_language = validated_output["language"]
    if provider_language == "unknown":
        provider_language = language

    if validated_output["refusal_status"] == "refused":
        return _provider_refusal_draft(
            latest_inbound_text=latest_inbound_text,
            language=provider_language,
            source=f"provider_refusal:{provider_name}",
            reason=validated_output["why_this_reply"],
        )

    return _draft(
        status="ready",
        latest_inbound_text=latest_inbound_text,
        reply_text=validated_output["draft_text"],
        language=provider_language,
        source=f"provider:{provider_name}",
        safety_note=(
            "Draft only. The operator checks context, facts, tone and "
            "safety before copying."
        ),
        tone_note=validated_output["why_this_reply"] or (
            "Check whether the draft matches the visible context."
        ),
    )
