from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any


MAX_DRAFT_TEXT_LENGTH = 4000
MAX_EXPLANATION_LENGTH = 800
MAX_LIST_ITEMS = 5
MAX_LIST_ITEM_LENGTH = 240

ALLOWED_LANGUAGES = {
    "nl",
    "en",
    "de",
    "pt",
    "unknown",
}
ALLOWED_COMMERCIAL_SIGNALS = {
    "none",
    "low",
    "medium",
    "high",
    "unknown",
}
ALLOWED_REFUSAL_STATUSES = {
    "none",
    "refused",
}


class BuddyOutputValidationError(ValueError):
    """Raised when provider output violates the Buddy output contract."""


@dataclass(frozen=True)
class ValidatedBuddyOutput:
    draft_text: str
    language: str
    why_this_reply: str
    open_loops_to_watch: list[str]
    do_not_do_warnings: list[str]
    commercial_signal: str
    confidence: float | None
    refusal_status: str


def _optional_string(
    payload: Mapping[str, Any],
    key: str,
    *,
    max_length: int,
) -> str:
    if key not in payload or payload[key] is None:
        return ""

    value = payload[key]

    if not isinstance(value, str):
        raise BuddyOutputValidationError(
            f"{key} must be a string."
        )

    normalized = value.strip()

    if len(normalized) > max_length:
        raise BuddyOutputValidationError(
            f"{key} exceeds the maximum length."
        )

    return normalized


def _enum_value(
    payload: Mapping[str, Any],
    key: str,
    *,
    allowed_values: set[str],
    default: str,
) -> str:
    value = _optional_string(
        payload,
        key,
        max_length=40,
    ) or default

    if value not in allowed_values:
        raise BuddyOutputValidationError(
            f"{key} contains an unsupported value."
        )

    return value


def _optional_confidence(
    payload: Mapping[str, Any],
) -> float | None:
    if "confidence" not in payload:
        return None

    value = payload["confidence"]

    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise BuddyOutputValidationError(
            "confidence must be a number."
        )

    normalized = float(value)

    if not 0.0 <= normalized <= 1.0:
        raise BuddyOutputValidationError(
            "confidence must be between 0 and 1."
        )

    return normalized


def _bounded_string_list(
    payload: Mapping[str, Any],
    key: str,
) -> list[str]:
    if key not in payload or payload[key] is None:
        return []

    values = payload[key]

    if not isinstance(values, list):
        raise BuddyOutputValidationError(
            f"{key} must be a list."
        )

    normalized = []

    # Valideer alle items, ook wanneer alleen de eerste vijf
    # uiteindelijk in het veilige resultaat terechtkomen.
    for value in values:
        if not isinstance(value, str):
            raise BuddyOutputValidationError(
                f"{key} may contain strings only."
            )

        item = value.strip()

        if len(item) > MAX_LIST_ITEM_LENGTH:
            raise BuddyOutputValidationError(
                f"{key} contains an item that is too long."
            )

        if item:
            normalized.append(item)

    return normalized[:MAX_LIST_ITEMS]


def validate_buddy_output(
    provider_result: Any,
) -> dict[str, Any]:
    """Validate and normalize untrusted Buddy provider output.

    Unknown provider fields are intentionally discarded.
    """

    if not isinstance(provider_result, Mapping):
        raise BuddyOutputValidationError(
            "Provider output must be a mapping."
        )

    refusal_status = _enum_value(
        provider_result,
        "refusal_status",
        allowed_values=ALLOWED_REFUSAL_STATUSES,
        default="none",
    )

    draft_text = _optional_string(
        provider_result,
        "draft_text",
        max_length=MAX_DRAFT_TEXT_LENGTH,
    )

    if refusal_status == "none" and not draft_text:
        raise BuddyOutputValidationError(
            "A normal provider response requires draft_text."
        )

    if refusal_status == "refused" and draft_text:
        raise BuddyOutputValidationError(
            "A refused provider response may not contain draft_text."
        )

    validated = ValidatedBuddyOutput(
        draft_text=draft_text,
        language=_enum_value(
            provider_result,
            "language",
            allowed_values=ALLOWED_LANGUAGES,
            default="unknown",
        ),
        why_this_reply=_optional_string(
            provider_result,
            "why_this_reply",
            max_length=MAX_EXPLANATION_LENGTH,
        ),
        open_loops_to_watch=_bounded_string_list(
            provider_result,
            "open_loops_to_watch",
        ),
        do_not_do_warnings=_bounded_string_list(
            provider_result,
            "do_not_do_warnings",
        ),
        commercial_signal=_enum_value(
            provider_result,
            "commercial_signal",
            allowed_values=ALLOWED_COMMERCIAL_SIGNALS,
            default="unknown",
        ),
        confidence=_optional_confidence(provider_result),
        refusal_status=refusal_status,
    )

    return asdict(validated)
