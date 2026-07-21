import re
from dataclasses import dataclass
from typing import Any


DEFAULT_CONTACT_REPLACEMENT = "##########"

_EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])"
    r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+"
    r"(?![\w-])",
    re.IGNORECASE,
)

_PHONE_CANDIDATE_PATTERN = re.compile(
    r"(?<!\w)(?:(?:\+|00)?\d[\d\s().-]{6,}\d)(?!\w)"
)


@dataclass(frozen=True)
class ContactDataSanitizationResult:
    sanitized_text: str
    changed: bool
    match_types: tuple[str, ...]


def _is_plausible_phone(candidate: str) -> bool:
    digits = "".join(
        character
        for character in candidate
        if character.isdigit()
    )
    digit_count = len(digits)
    stripped = candidate.lstrip()

    has_international_prefix = (
        stripped.startswith("+")
        or stripped.startswith("00")
    )
    starts_with_zero = digits.startswith("0")
    has_separator = any(
        not character.isdigit()
        for character in stripped.lstrip("+")
    )

    if not 8 <= digit_count <= 16:
        return False

    if has_international_prefix:
        return True

    if starts_with_zero:
        return digit_count >= 9

    return has_separator and digit_count >= 10


def sanitize_contact_data(
    value: Any,
    *,
    email_replacement: str = DEFAULT_CONTACT_REPLACEMENT,
    phone_replacement: str = DEFAULT_CONTACT_REPLACEMENT,
) -> ContactDataSanitizationResult:
    """Replace recognizable email addresses and phone numbers.

    The result never contains the original matches as metadata.
    No logging, storage or network activity occurs.
    """

    original_text = (
        ""
        if value is None
        else str(value)
    )

    detected = {
        "email": False,
        "phone": False,
    }

    def replace_email(match: re.Match[str]) -> str:
        detected["email"] = True
        return str(email_replacement)

    def replace_phone(match: re.Match[str]) -> str:
        candidate = match.group(0)

        if not _is_plausible_phone(candidate):
            return candidate

        detected["phone"] = True
        return str(phone_replacement)

    sanitized_text = _EMAIL_PATTERN.sub(
        replace_email,
        original_text,
    )
    sanitized_text = _PHONE_CANDIDATE_PATTERN.sub(
        replace_phone,
        sanitized_text,
    )

    match_types = tuple(
        match_type
        for match_type in ("email", "phone")
        if detected[match_type]
    )

    return ContactDataSanitizationResult(
        sanitized_text=sanitized_text,
        changed=sanitized_text != original_text,
        match_types=match_types,
    )
