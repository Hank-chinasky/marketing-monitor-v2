import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)


DEFAULT_VENICE_API_BASE = "https://api.venice.ai/api/v1"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_RESPONSE_BYTES = 262_144

MIN_TIMEOUT_SECONDS = 1.0
MAX_TIMEOUT_SECONDS = 60.0
MIN_RESPONSE_BYTES = 4_096
MAX_RESPONSE_BYTES = 1_048_576
MAX_REQUEST_BYTES = 65_536
MAX_API_KEY_LENGTH = 4_096

VENICE_CHAT_PATH = "/chat/completions"
VENICE_ALLOWED_HOST = "api.venice.ai"

BUDDY_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "draft_text": {
            "type": "string",
            "maxLength": 4000,
        },
        "language": {
            "type": "string",
            "enum": [
                "nl",
                "en",
                "de",
                "pt",
                "unknown",
            ],
        },
        "why_this_reply": {
            "type": "string",
            "maxLength": 800,
        },
        "open_loops_to_watch": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "string",
                "maxLength": 240,
            },
        },
        "do_not_do_warnings": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "string",
                "maxLength": 240,
            },
        },
        "commercial_signal": {
            "type": "string",
            "enum": [
                "none",
                "low",
                "medium",
                "high",
                "unknown",
            ],
        },
        "confidence": {
            "type": [
                "number",
                "null",
            ],
            "minimum": 0,
            "maximum": 1,
        },
        "refusal_status": {
            "type": "string",
            "enum": [
                "none",
                "refused",
            ],
        },
    },
    "required": [
        "draft_text",
        "language",
        "why_this_reply",
        "open_loops_to_watch",
        "do_not_do_warnings",
        "commercial_signal",
        "confidence",
        "refusal_status",
    ],
}


class VeniceConfigurationError(RuntimeError):
    """Raised for invalid or incomplete Venice configuration."""


class VeniceProviderError(RuntimeError):
    """Raised when Venice cannot produce a controlled provider result."""


class VeniceTransport(Protocol):
    def __call__(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes:
        """Execute one bounded Venice request and return raw response bytes."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        request,
        file_pointer,
        code,
        message,
        headers,
        new_url,
    ):
        return None


def _validate_api_base(value: Any) -> str:
    api_base = str(value or "").strip().rstrip("/")

    if not api_base:
        raise VeniceConfigurationError(
            "Venice API base is missing."
        )

    try:
        parsed = urlsplit(api_base)
        port = parsed.port
    except ValueError:
        raise VeniceConfigurationError(
            "Venice API base is invalid."
        ) from None

    if (
        parsed.scheme != "https"
        or parsed.hostname != VENICE_ALLOWED_HOST
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != "/api/v1"
    ):
        raise VeniceConfigurationError(
            "Venice API base is not allowed."
        )

    return DEFAULT_VENICE_API_BASE


def _parse_float_setting(
    value: Any,
    *,
    default: float,
    minimum: float,
    maximum: float,
    setting_name: str,
) -> float:
    raw_value = (
        ""
        if value is None
        else str(value).strip()
    )

    if not raw_value:
        return default

    try:
        normalized = float(raw_value)
    except ValueError:
        raise VeniceConfigurationError(
            f"{setting_name} is invalid."
        ) from None

    if not minimum <= normalized <= maximum:
        raise VeniceConfigurationError(
            f"{setting_name} is outside the allowed range."
        )

    return normalized


def _parse_int_setting(
    value: Any,
    *,
    default: int,
    minimum: int,
    maximum: int,
    setting_name: str,
) -> int:
    raw_value = (
        ""
        if value is None
        else str(value).strip()
    )

    if not raw_value:
        return default

    try:
        normalized = int(raw_value)
    except ValueError:
        raise VeniceConfigurationError(
            f"{setting_name} is invalid."
        ) from None

    if not minimum <= normalized <= maximum:
        raise VeniceConfigurationError(
            f"{setting_name} is outside the allowed range."
        )

    return normalized


def _validate_api_key(value: Any) -> str:
    api_key = str(value or "").strip()

    if not api_key:
        raise VeniceConfigurationError(
            "Venice API key is missing."
        )

    if (
        len(api_key) > MAX_API_KEY_LENGTH
        or any(
            character.isspace()
            or ord(character) < 33
            for character in api_key
        )
    ):
        raise VeniceConfigurationError(
            "Venice API key is invalid."
        )

    return api_key


def _validate_model(value: Any) -> str:
    model = str(value or "").strip()

    if not model:
        raise VeniceConfigurationError(
            "Venice model is missing."
        )

    if (
        len(model) > 200
        or any(character.isspace() for character in model)
        or any(ord(character) < 32 for character in model)
    ):
        raise VeniceConfigurationError(
            "Venice model is invalid."
        )

    return model


def _read_limited_response(
    response,
    *,
    max_response_bytes: int,
) -> bytes:
    content_type = str(
        response.headers.get("Content-Type", "")
    ).lower()

    if not content_type.startswith("application/json"):
        raise VeniceProviderError(
            "Venice returned an unsupported content type."
        )

    content_length = response.headers.get("Content-Length")

    if content_length:
        try:
            declared_length = int(content_length)
        except (TypeError, ValueError):
            raise VeniceProviderError(
                "Venice returned an invalid response length."
            ) from None

        if declared_length > max_response_bytes:
            raise VeniceProviderError(
                "Venice response exceeded the allowed size."
            )

    response_bytes = response.read(max_response_bytes + 1)

    if not isinstance(response_bytes, bytes):
        raise VeniceProviderError(
            "Venice returned an invalid response body."
        )

    if len(response_bytes) > max_response_bytes:
        raise VeniceProviderError(
            "Venice response exceeded the allowed size."
        )

    return response_bytes


def default_venice_transport(
    *,
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout_seconds: float,
    max_response_bytes: int,
) -> bytes:
    """Execute one non-streaming request without following redirects."""

    request = Request(
        url=url,
        data=body,
        headers=dict(headers),
        method="POST",
    )
    opener = build_opener(_NoRedirectHandler())

    try:
        with opener.open(
            request,
            timeout=timeout_seconds,
        ) as response:
            status = int(getattr(response, "status", 200))

            if status != 200:
                raise VeniceProviderError(
                    "Venice returned a non-success response."
                )

            return _read_limited_response(
                response,
                max_response_bytes=max_response_bytes,
            )
    except VeniceProviderError:
        raise
    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
    ):
        raise VeniceProviderError(
            "Venice request failed."
        ) from None


def _build_system_prompt() -> str:
    return (
        "You are Buddy, a controlled operator colleague inside "
        "CreatorWorkboardFlow. Use only the supplied context packet. "
        "Create one concise reply draft that continues the conversation "
        "naturally and respects profile tone, open loops and do-not-do "
        "warnings. Never invent customer facts, promises, payments or "
        "platform actions. Never expose or reconstruct contact details. "
        "Do not send anything and do not claim that anything was sent. "
        "Human operator review is always required. When context is too "
        "weak or unsafe, set refusal_status to refused and draft_text to "
        "an empty string. Return only the required JSON object."
    )


def _build_request_payload(
    *,
    model: str,
    context_packet: Mapping[str, Any],
) -> dict[str, Any]:
    context_json = json.dumps(
        dict(context_packet),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )

    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": _build_system_prompt(),
            },
            {
                "role": "user",
                "content": (
                    "Controlled BuddyContextPacket:\n"
                    f"{context_json}"
                ),
            },
        ],
        "stream": False,
        "store": False,
        "n": 1,
        "temperature": 0.25,
        "max_completion_tokens": 900,
        "parallel_tool_calls": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "buddy_reply_v1",
                "strict": True,
                "schema": BUDDY_RESPONSE_SCHEMA,
            },
        },
        "venice_parameters": {
            "include_venice_system_prompt": False,
            "enable_web_search": "off",
            "enable_web_scraping": False,
            "enable_web_citations": False,
            "enable_x_search": False,
        },
    }


def _decode_json_mapping(
    value: bytes | str,
    *,
    error_message: str,
) -> dict[str, Any]:
    try:
        if isinstance(value, bytes):
            decoded_value = value.decode("utf-8")
        elif isinstance(value, str):
            decoded_value = value
        else:
            raise TypeError

        parsed = json.loads(decoded_value)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
    ):
        raise VeniceProviderError(
            error_message
        ) from None

    if not isinstance(parsed, Mapping):
        raise VeniceProviderError(
            error_message
        )

    return dict(parsed)


def _extract_structured_content(
    response_payload: Mapping[str, Any],
) -> dict[str, Any]:
    choices = response_payload.get("choices")

    if not isinstance(choices, list) or not choices:
        raise VeniceProviderError(
            "Venice response contained no usable choice."
        )

    first_choice = choices[0]

    if not isinstance(first_choice, Mapping):
        raise VeniceProviderError(
            "Venice response contained no usable choice."
        )

    message = first_choice.get("message")

    if not isinstance(message, Mapping):
        raise VeniceProviderError(
            "Venice response contained no usable message."
        )

    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise VeniceProviderError(
            "Venice response contained no structured content."
        )

    return _decode_json_mapping(
        content,
        error_message=(
            "Venice returned invalid structured content."
        ),
    )


@dataclass(frozen=True)
class VeniceBuddyProvider:
    api_key: str = field(repr=False)
    model: str
    api_base: str = DEFAULT_VENICE_API_BASE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES
    transport: VeniceTransport = field(
        default=default_venice_transport,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        api_key = _validate_api_key(
            self.api_key
        )
        model = _validate_model(
            self.model
        )
        api_base = _validate_api_base(
            self.api_base
        )
        timeout_seconds = _parse_float_setting(
            self.timeout_seconds,
            default=DEFAULT_TIMEOUT_SECONDS,
            minimum=MIN_TIMEOUT_SECONDS,
            maximum=MAX_TIMEOUT_SECONDS,
            setting_name="timeout_seconds",
        )
        max_response_bytes = _parse_int_setting(
            self.max_response_bytes,
            default=DEFAULT_MAX_RESPONSE_BYTES,
            minimum=MIN_RESPONSE_BYTES,
            maximum=MAX_RESPONSE_BYTES,
            setting_name="max_response_bytes",
        )

        if not callable(self.transport):
            raise VeniceConfigurationError(
                "Venice transport is invalid."
            )

        object.__setattr__(
            self,
            "api_key",
            api_key,
        )
        object.__setattr__(
            self,
            "model",
            model,
        )
        object.__setattr__(
            self,
            "api_base",
            api_base,
        )
        object.__setattr__(
            self,
            "timeout_seconds",
            timeout_seconds,
        )
        object.__setattr__(
            self,
            "max_response_bytes",
            max_response_bytes,
        )

    def generate_reply(
        self,
        *,
        context_packet: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        request_payload = _build_request_payload(
            model=self.model,
            context_packet=context_packet,
        )

        try:
            request_body = json.dumps(
                request_payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (
            TypeError,
            ValueError,
        ):
            raise VeniceProviderError(
                "Buddy context could not be encoded safely."
            ) from None

        if len(request_body) > MAX_REQUEST_BYTES:
            raise VeniceProviderError(
                "Buddy request exceeded the allowed size."
            )

        endpoint_base = _validate_api_base(
            self.api_base
        )
        endpoint = (
            f"{endpoint_base}{VENICE_CHAT_PATH}"
        )

        try:
            response_bytes = self.transport(
                url=endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": (
                        "CreatorWorkboard-Buddy/1.0"
                    ),
                },
                body=request_body,
                timeout_seconds=self.timeout_seconds,
                max_response_bytes=self.max_response_bytes,
            )
        except VeniceProviderError:
            raise
        except Exception:
            raise VeniceProviderError(
                "Venice request failed."
            ) from None

        response_payload = _decode_json_mapping(
            response_bytes,
            error_message=(
                "Venice returned an invalid JSON response."
            ),
        )

        return _extract_structured_content(
            response_payload
        )


def build_venice_provider_from_environment(
    *,
    transport: VeniceTransport | None = None,
) -> VeniceBuddyProvider:
    api_key = _validate_api_key(
        os.getenv("VENICE_API_KEY", "")
    )

    model = _validate_model(
        os.getenv("VENICE_MODEL", "")
    )
    api_base = _validate_api_base(
        os.getenv(
            "VENICE_API_BASE",
            DEFAULT_VENICE_API_BASE,
        )
    )
    timeout_seconds = _parse_float_setting(
        os.getenv("VENICE_TIMEOUT_SECONDS", ""),
        default=DEFAULT_TIMEOUT_SECONDS,
        minimum=MIN_TIMEOUT_SECONDS,
        maximum=MAX_TIMEOUT_SECONDS,
        setting_name="VENICE_TIMEOUT_SECONDS",
    )
    max_response_bytes = _parse_int_setting(
        os.getenv("VENICE_MAX_RESPONSE_BYTES", ""),
        default=DEFAULT_MAX_RESPONSE_BYTES,
        minimum=MIN_RESPONSE_BYTES,
        maximum=MAX_RESPONSE_BYTES,
        setting_name="VENICE_MAX_RESPONSE_BYTES",
    )

    return VeniceBuddyProvider(
        api_key=api_key,
        model=model,
        api_base=api_base,
        timeout_seconds=timeout_seconds,
        max_response_bytes=max_response_bytes,
        transport=transport or default_venice_transport,
    )
