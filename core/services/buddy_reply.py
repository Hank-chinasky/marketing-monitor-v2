from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class OperatorReplyDraft:
    reply_text: str
    language: str
    source: str
    requires_human_review: bool
    safety_note: str


def _text(value) -> str:
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


def _detect_language(text: str) -> str:
    lowered = _text(text).lower()
    if not lowered:
        return "unknown"

    portuguese_markers = {
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
    }
    dutch_markers = {
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
    }

    if any(marker in lowered for marker in portuguese_markers):
        return "pt"
    if any(marker in lowered for marker in dutch_markers):
        return "nl"
    return "en"


def _reply_text_for_language(language: str) -> str:
    if language == "pt":
        return "Obrigado pela mensagem. Vou verificar isto com cuidado e volto com uma resposta."
    if language == "nl":
        return "Dankjewel voor je bericht. Ik kijk dit zorgvuldig na en kom hierop terug."
    return "Thanks for your message. I will review this carefully and get back to you."


def _draft(reply_text: str, language: str, source: str, safety_note: str) -> dict[str, Any]:
    return asdict(
        OperatorReplyDraft(
            reply_text=reply_text,
            language=language,
            source=source,
            requires_human_review=True,
            safety_note=safety_note,
        )
    )


def build_operator_reply_draft(
    selected_thread,
    conversation_messages,
    *,
    latest_draft=None,
    operator=None,
) -> dict[str, Any]:
    """Build a conservative, operator-facing reply draft snapshot.

    This function is intentionally deterministic and read-only. It does not create
    BuddyDraft rows, call external providers, send messages, or decide whether an
    operator may act. Future provider/model replacement should happen behind this
    service boundary.
    """

    if not selected_thread:
        return _draft(
            reply_text="",
            language="unknown",
            source="no_thread",
            safety_note="Geen actieve thread geselecteerd; er is geen reply draft beschikbaar.",
        )

    latest_inbound_body = _latest_inbound_body(conversation_messages)
    language = _detect_language(latest_inbound_body)

    existing_reply_text = _text(getattr(latest_draft, "reply_text", ""))
    if existing_reply_text:
        return _draft(
            reply_text=existing_reply_text,
            language=language,
            source="latest_buddy_draft",
            safety_note="Bestaand BuddyDraft overgenomen als read-only operatorconcept; handmatige review blijft verplicht.",
        )

    if not latest_inbound_body:
        return _draft(
            reply_text="",
            language="unknown",
            source="no_inbound_message",
            safety_note="Geen inbound klantbericht beschikbaar; maak geen reply draft zonder klantcontext.",
        )

    return _draft(
        reply_text=_reply_text_for_language(language),
        language=language,
        source="deterministic_stub",
        safety_note="Deterministisch intern concept; operator moet context, policy en toon handmatig controleren.",
    )
