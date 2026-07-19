from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from core.services.buddy_context import build_buddy_context_packet


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
    "no_thread": ("Geen gesprek", "badge-yellow"),
    "no_inbound_message": ("Geen klantbericht", "badge-yellow"),
    "existing_draft": ("Bestaand Buddy-concept", "badge-blue"),
    "provider_unavailable": ("Nog geen Buddy-antwoord", "badge-yellow"),
    "provider_error": ("Providerfout", "badge-red"),
    "ready": ("Concept gereed", "badge-green"),
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
            "De Buddy-provider kon geen geldig concept leveren. "
            "Er is geen automatisch of generiek antwoord ingevuld."
        ),
        safety_note=(
            "Geen provideruitvoer beschikbaar. "
            "De operator moet zelf beslissen of handmatig antwoorden veilig is."
        ),
        tone_note="Controleer providerstatus en context voordat je verdergaat.",
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
                "Geen actieve thread geselecteerd. "
                "Er mag geen antwoord worden gebruikt."
            ),
            missing_context_note="Geen actieve thread geselecteerd.",
            tone_note="Selecteer eerst een gesprek.",
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
                "Er is geen inkomend klantbericht beschikbaar. "
                "Er mag geen antwoord worden gebruikt."
            ),
            missing_context_note="Geen inkomend klantbericht beschikbaar.",
            tone_note="Wacht op klantcontext voordat je een antwoord opstelt.",
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
                "Concept alleen. De operator moet het bestaande Buddy-concept "
                "controleren tegen de zichtbare berichten en context."
            ),
            tone_note=(
                "Controleer of het bestaande concept de laatste klantboodschap, "
                "profieltoon en open loop correct volgt."
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
                "Er is geen Buddy-provider gekoppeld. "
                "Een handmatig ingevoerd concept is geen AI-uitvoer."
            ),
            tone_note=(
                "De operator kan handmatig een concept typen, maar Buddy heeft "
                "in deze staat geen antwoord gegenereerd."
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

    if not isinstance(provider_result, Mapping):
        return _provider_error_draft(
            latest_inbound_text=latest_inbound_text,
            language=language,
            source=f"provider_error:{provider_name}",
        )

    reply_text = _text(provider_result.get("draft_text"))

    if not reply_text:
        return _provider_error_draft(
            latest_inbound_text=latest_inbound_text,
            language=language,
            source=f"provider_error:{provider_name}",
        )

    provider_language = _text(provider_result.get("language")) or language
    why_this_reply = _text(provider_result.get("why_this_reply"))

    return _draft(
        status="ready",
        latest_inbound_text=latest_inbound_text,
        reply_text=reply_text,
        language=provider_language,
        source=_text(provider_result.get("source")) or f"provider:{provider_name}",
        safety_note=(
            "Concept alleen. De operator controleert context, feiten, toon en "
            "veiligheid vóór kopiëren."
        ),
        tone_note=why_this_reply or (
            "Controleer of het concept aansluit op de zichtbare context."
        ),
    )
