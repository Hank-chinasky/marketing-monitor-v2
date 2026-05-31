from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class OperatorReplyDraft:
    reply_text: str
    language: str
    source: str
    requires_human_review: bool
    safety_note: str
    missing_context_note: str
    tone_note: str


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


def _marker_score(text: str, markers: set[str]) -> int:
    return sum(1 for marker in markers if marker in text)


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
        "helpen",
    }
    german_markers = {
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
    }
    english_markers = {
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
    }

    scores = {
        "pt": _marker_score(lowered, portuguese_markers),
        "nl": _marker_score(lowered, dutch_markers),
        "de": _marker_score(lowered, german_markers),
        "en": _marker_score(lowered, english_markers),
    }

    best_language, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score > 0:
        return best_language

    return "en"


def _reply_text_for_language(language: str) -> str:
    if language == "pt":
        return "Obrigado pela mensagem. Vou verificar isto com cuidado e volto com uma resposta adequada."
    if language == "nl":
        return "Dankjewel voor je bericht. Ik kijk even goed naar je vraag en kom zo met een zorgvuldig antwoord terug."
    if language == "de":
        return "Danke für deine Nachricht. Ich schaue mir deine Frage sorgfältig an und komme gleich mit einer passenden Antwort zurück."
    return "Thanks for your message. I’ll review your question carefully and come back with a clear reply."


def _draft(
    *,
    reply_text: str,
    language: str,
    source: str,
    safety_note: str,
    missing_context_note: str = "",
    tone_note: str = "",
) -> dict[str, Any]:
    return asdict(
        OperatorReplyDraft(
            reply_text=reply_text,
            language=language,
            source=source,
            requires_human_review=True,
            safety_note=safety_note,
            missing_context_note=missing_context_note,
            tone_note=tone_note,
        )
    )


def build_operator_reply_draft(
    selected_thread,
    conversation_messages,
    *,
    latest_draft=None,
    operator=None,
) -> dict[str, Any]:
    """Build a deterministic, operator-facing reply draft snapshot.

    This function is intentionally read-only. It does not create BuddyDraft rows,
    call external providers, send messages, or decide whether an operator may
    act. Future provider/model replacement should happen behind this service
    boundary.
    """

    if not selected_thread:
        return _draft(
            reply_text="",
            language="unknown",
            source="no_thread",
            safety_note="Draft only. No active thread is selected, so no reply should be used.",
            missing_context_note="No active thread selected.",
            tone_note="No draft should be used until thread context is available.",
        )

    latest_inbound_body = _latest_inbound_body(conversation_messages)
    language = _detect_language(latest_inbound_body)

    existing_reply_text = _text(getattr(latest_draft, "reply_text", ""))
    if existing_reply_text:
        return _draft(
            reply_text=existing_reply_text,
            language=language,
            source="latest_buddy_draft",
            safety_note="Draft only. Operator must review the existing draft against the latest visible messages before use.",
            missing_context_note="",
            tone_note="Review the existing draft against the latest visible messages before use.",
        )

    if not latest_inbound_body:
        return _draft(
            reply_text="",
            language="unknown",
            source="no_inbound_message",
            safety_note="Draft only. No inbound customer message is available, so no reply should be used.",
            missing_context_note="No inbound customer message is available.",
            tone_note="Wait for customer context before drafting a reply.",
        )

    return _draft(
        reply_text=_reply_text_for_language(language),
        language=language,
        source="deterministic_quality_v1",
        safety_note="Draft only. Operator must review context, policy and tone before using this reply.",
        missing_context_note="",
        tone_note="Keep the reply short, careful and aligned with the visible context.",
    )
