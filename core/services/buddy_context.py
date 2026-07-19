from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
import re
from typing import Any


BUDDY_CONTEXT_SCHEMA_VERSION = "buddy-context-v1"
DEFAULT_RECENT_MESSAGE_LIMIT = 8

_EMAIL_PATTERN = re.compile(
    r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b",
)
_PHONE_CANDIDATE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d[\d\s().-]{6,}\d)(?!\w)"
)


@dataclass(frozen=True)
class BuddyContextMessage:
    direction: str
    body: str
    occurred_at: str
    source_platform: str


@dataclass(frozen=True)
class BuddyContextPacket:
    schema_version: str
    thread_status: str
    source_platform: str
    source_account: str
    profile_name: str
    language: str
    latest_inbound_text: str
    recent_messages: list[dict[str, str]]
    thread_summary: str
    profile_tone: str
    open_loop: str
    do_not_do: str
    recommended_next_action: str
    reliability: dict[str, str]
    missing_context: list[str]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _mask_phone_candidate(match: re.Match[str]) -> str:
    candidate = match.group(0)
    digit_count = sum(character.isdigit() for character in candidate)
    has_international_prefix = candidate.lstrip().startswith("+")

    if digit_count >= 9:
        return "[phone]"

    if has_international_prefix and digit_count >= 8:
        return "[phone]"

    return candidate


def _redact_sensitive_text(value: Any) -> str:
    text = _text(value)
    if not text:
        return ""

    text = _EMAIL_PATTERN.sub("[email]", text)
    text = _PHONE_CANDIDATE_PATTERN.sub(
        _mask_phone_candidate,
        text,
    )
    return text


def _timestamp(value: Any) -> str:
    if value is None:
        return ""

    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()

    return _text(value)


def _message_direction(message: Any) -> str:
    return _text(getattr(message, "direction", ""))


def _message_body(message: Any) -> str:
    return _redact_sensitive_text(
        getattr(message, "body", "")
    )


def _latest_inbound_text(messages: Iterable[Any]) -> str:
    for message in reversed(list(messages or [])):
        if _message_direction(message) != "inbound":
            continue

        body = _message_body(message)
        if body:
            return body

    return ""


def _safe_recent_messages(
    messages: Iterable[Any],
    *,
    default_source_platform: str,
    limit: int,
) -> list[dict[str, str]]:
    safe_messages = []

    for message in messages or []:
        direction = _message_direction(message)

        # Interne notities en onbekende richtingen worden uitgesloten.
        if direction not in {"inbound", "outbound"}:
            continue

        body = _message_body(message)
        if not body:
            continue

        source_platform = (
            _text(getattr(message, "source_system", ""))
            or default_source_platform
        )

        safe_messages.append(
            asdict(
                BuddyContextMessage(
                    direction=direction,
                    body=body,
                    occurred_at=_timestamp(
                        getattr(message, "occurred_at", None)
                    ),
                    source_platform=source_platform,
                )
            )
        )

    requested_limit = max(1, int(limit or 1))
    safe_limit = min(
        DEFAULT_RECENT_MESSAGE_LIMIT,
        requested_limit,
    )
    return safe_messages[-safe_limit:]


def _safe_missing_context(values: Iterable[Any]) -> list[str]:
    result = []

    for value in values or []:
        redacted = _redact_sensitive_text(value)
        if redacted:
            result.append(redacted)

    return result


def build_buddy_context_packet(
    selected_thread: Any,
    conversation_messages: Iterable[Any],
    *,
    buddy_assist: Mapping[str, Any] | None = None,
    language: str = "unknown",
    recent_message_limit: int = DEFAULT_RECENT_MESSAGE_LIMIT,
) -> dict[str, Any]:
    """Build minimal, serializable and stateless Buddy provider context.

    Django objects, operator objects, credentials, access notes, URLs,
    source thread IDs and participant IDs are not returned.
    """

    messages = list(conversation_messages or [])
    assist = dict(buddy_assist or {})

    channel = getattr(selected_thread, "channel", None)
    creator = getattr(selected_thread, "creator", None)

    source_platform = _text(
        getattr(selected_thread, "source_system", "")
    )

    source_account = _redact_sensitive_text(
        _text(getattr(selected_thread, "source_site_label", ""))
        or _text(getattr(channel, "handle", ""))
    )

    profile_name = _redact_sensitive_text(
        _text(getattr(channel, "handle", ""))
        or _text(getattr(creator, "display_name", ""))
    )

    packet = BuddyContextPacket(
        schema_version=BUDDY_CONTEXT_SCHEMA_VERSION,
        thread_status=_text(
            getattr(selected_thread, "status", "")
        ),
        source_platform=source_platform,
        source_account=source_account,
        profile_name=profile_name,
        language=_text(language) or "unknown",
        latest_inbound_text=_latest_inbound_text(messages),
        recent_messages=_safe_recent_messages(
            messages,
            default_source_platform=source_platform,
            limit=recent_message_limit,
        ),
        thread_summary=_redact_sensitive_text(
            assist.get("thread_summary")
            or getattr(selected_thread, "thread_summary", "")
        ),
        profile_tone=_redact_sensitive_text(
            assist.get("profile_tone")
            or getattr(
                selected_thread,
                "last_approved_reply_style",
                "",
            )
        ),
        open_loop=_redact_sensitive_text(
            assist.get("open_loop")
            or getattr(selected_thread, "open_loop", "")
        ),
        do_not_do=_redact_sensitive_text(
            assist.get("do_not_do", "")
        ),
        recommended_next_action=_redact_sensitive_text(
            assist.get("recommended_next_action", "")
        ),
        reliability={
            "label": _text(
                assist.get("reliability_label")
            ),
            "reason": _redact_sensitive_text(
                assist.get("reliability_reason", "")
            ),
        },
        missing_context=_safe_missing_context(
            assist.get("missing_context", [])
        ),
    )

    return asdict(packet)
