import hashlib
import hmac
import json
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import (
    ConversationContextSnapshot,
    ConversationThread,
)


SCHEMA_VERSION = "eurotikken-operator-context-v1"

EXPECTED_SOURCE = {
    "source_system": "eurotikken",
    "source_site_id": "25",
    "source_profile_id": "2390",
    "source_customer_id": "60010",
    "source_customer_user_id": "60055",
    "source_thread_id": "eurotikken:25:2390:60010",
}

ALLOWED_MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MEDIA_POLICY_REQUIREMENTS = {
    "binary_content_included": False,
    "load_only_after_operator_action": True,
    "allow_external_ai": False,
    "allow_automatic_image_analysis": False,
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CommandError(f"{label} must be an object.")
    return value


def _require_boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise CommandError(f"{label} must be boolean.")
    return value


def _normalize_age(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CommandError(f"{label} must be an integer.")
    if not 18 <= value <= 130:
        raise CommandError(f"{label} is outside the accepted range.")
    return value


def _normalize_marital_status(value: Any) -> str:
    if isinstance(value, dict):
        return _text(value.get("value"))
    return _text(value)


def _normalize_context(
    value: Any,
    *,
    label: str,
    expected_profile_id: str,
    expected_user_id: str | None = None,
) -> dict[str, Any]:
    context = _require_mapping(value, label)

    nested_profile_id = _text(context.get("source_profile_id"))
    if nested_profile_id != expected_profile_id:
        raise CommandError(
            f"{label}.source_profile_id mismatch: "
            f"expected {expected_profile_id}."
        )

    if expected_user_id is not None:
        nested_user_id = _text(context.get("source_user_id"))
        if nested_user_id != expected_user_id:
            raise CommandError(
                f"{label}.source_user_id mismatch: "
                f"expected {expected_user_id}."
            )

    return {
        "display_name": _text(context.get("display_name")),
        "age": _normalize_age(context.get("age"), f"{label}.age"),
        "city": _text(context.get("city")),
        "region": _text(context.get("region")),
        "country": _text(context.get("country")),
        "marital_status": _normalize_marital_status(
            context.get("marital_status")
        ),
        "goal": _text(context.get("goal")),
        "occupation": _text(context.get("occupation")),
        "summary": _text(context.get("profile_summary")),
        "source_checked": _require_boolean(
            context.get("source_checked"),
            f"{label}.source_checked",
        ),
        "source_reviewed": _require_boolean(
            context.get("source_reviewed"),
            f"{label}.source_reviewed",
        ),
    }


def _validate_source_path(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise CommandError(f"{label} must be a string.")

    source_path = value.strip()

    if not source_path:
        raise CommandError(f"{label} may not be empty.")
    if "\\" in source_path:
        raise CommandError(f"{label} may not contain backslashes.")
    if "%" in source_path:
        raise CommandError(f"{label} may not contain encoded path data.")
    if "//" in source_path:
        raise CommandError(f"{label} may not contain an empty path segment.")
    if source_path.startswith("/"):
        raise CommandError(f"{label} must be relative.")
    if not source_path.startswith("uploaded_files/"):
        raise CommandError(
            f"{label} must start with uploaded_files/."
        )

    parsed = urlsplit(source_path)
    if (
        parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or parsed.path != source_path
    ):
        raise CommandError(f"{label} must be a plain relative path.")

    parts = PurePosixPath(source_path).parts
    if ".." in parts or "." in parts:
        raise CommandError(f"{label} contains an unsafe path segment.")
    if len(parts) < 2:
        raise CommandError(f"{label} must include a filename.")

    suffix = PurePosixPath(source_path).suffix.lower()
    if suffix not in ALLOWED_MEDIA_EXTENSIONS:
        raise CommandError(
            f"{label} has an unsupported image extension."
        )

    return source_path


def _normalize_media(
    value: Any,
    *,
    label: str,
    expected_owner_user_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise CommandError(f"{label} must be a list.")
    if len(value) > 10:
        raise CommandError(f"{label} may contain at most 10 records.")

    result = []

    for index, raw_item in enumerate(value):
        item_label = f"{label}[{index}]"
        item = _require_mapping(raw_item, item_label)

        if _text(item.get("media_type")).lower() != "image":
            raise CommandError(f"{item_label}.media_type must be image.")

        source_media_id = _text(item.get("source_media_id"))
        if not source_media_id.isdigit():
            raise CommandError(
                f"{item_label}.source_media_id must be numeric."
            )

        source_owner_user_id = _text(
            item.get("source_owner_user_id")
        )
        if not source_owner_user_id.isdigit():
            raise CommandError(
                f"{item_label}.source_owner_user_id must be numeric."
            )
        if source_owner_user_id != expected_owner_user_id:
            raise CommandError(
                f"{item_label}.source_owner_user_id mismatch: "
                f"expected {expected_owner_user_id}."
            )

        if item.get("allow_external_ai") is not False:
            raise CommandError(
                f"{item_label}.allow_external_ai must be false."
            )
        if item.get("requires_operator_reveal") is not True:
            raise CommandError(
                f"{item_label}.requires_operator_reveal must be true."
            )
        if _text(item.get("default_visibility")) != "covered":
            raise CommandError(
                f"{item_label}.default_visibility must be covered."
            )

        is_primary = item.get("is_primary", False)
        if not isinstance(is_primary, bool):
            raise CommandError(
                f"{item_label}.is_primary must be boolean."
            )

        active = item.get("active", True)
        active = _normalize_legacy_boolean(
            active,
            field_name=(
                f"{label}[{index}].active"
            ),
        )
        result.append(
            {
                "source_media_id": source_media_id,
                "source_owner_user_id": source_owner_user_id,
                "source_path": _validate_source_path(
                    item.get("source_path"),
                    f"{item_label}.source_path",
                ),
                "media_type": "image",
                "is_primary": is_primary,
                "active": active,
                "requires_operator_reveal": True,
                "default_visibility": "covered",
                "allow_external_ai": False,
            }
        )

    return result


def _normalize_data_quality(value: Any) -> dict[str, Any]:
    data_quality = _require_mapping(value, "data_quality")

    warnings = data_quality.get("warnings", [])
    if not isinstance(warnings, list):
        raise CommandError("data_quality.warnings must be a list.")

    normalized_warnings = []
    for index, raw_warning in enumerate(warnings[:50]):
        warning = _require_mapping(
            raw_warning,
            f"data_quality.warnings[{index}]",
        )
        normalized_warnings.append(
            {
                "code": _text(warning.get("code")),
                "field": _text(warning.get("field")),
                "resolution": _text(warning.get("resolution")),
            }
        )

    return {
        "profile_reliability": _text(
            data_quality.get("profile_reliability")
        ),
        "customer_reliability": _text(
            data_quality.get("customer_reliability")
        ),
        "warnings": normalized_warnings,
    }


def _validate_media_policy(value: Any) -> None:
    media_policy = _require_mapping(value, "media_policy")

    for key, expected in MEDIA_POLICY_REQUIREMENTS.items():
        if media_policy.get(key) is not expected:
            expected_label = str(expected).lower()
            raise CommandError(
                f"media_policy.{key} must be {expected_label}."
            )


def _normalize_legacy_boolean(
    value,
    *,
    field_name: str,
) -> bool:
    """Normalize only explicit boolean representations."""

    if isinstance(value, bool):
        return value

    if value == "Y":
        return True

    if value == "N":
        return False

    raise CommandError(
        f"{field_name} must be boolean or exact legacy Y/N."
    )


class Command(BaseCommand):
    help = (
        "Validate and optionally import one bounded Eurotikken "
        "operator-context snapshot."
    )

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True)
        parser.add_argument("--expected-sha256", required=True)
        parser.add_argument("--creator-id", required=True, type=int)
        parser.add_argument("--channel-id", required=True, type=int)
        parser.add_argument("--site-id", required=True)
        parser.add_argument("--profile-id", required=True)
        parser.add_argument("--customer-id", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        supplied_source_ids = {
            "source_site_id": _text(options["site_id"]),
            "source_profile_id": _text(options["profile_id"]),
            "source_customer_id": _text(options["customer_id"]),
        }

        for key, supplied_value in supplied_source_ids.items():
            expected_value = EXPECTED_SOURCE[key]
            if supplied_value != expected_value:
                raise CommandError(
                    f"{key} argument mismatch: expected {expected_value}."
                )

        input_path = Path(options["input"]).expanduser()
        try:
            raw_bytes = input_path.read_bytes()
        except OSError as exc:
            raise CommandError(
                f"Unable to read input file: {exc}"
            ) from exc

        actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        expected_sha256 = _text(
            options["expected_sha256"]
        ).lower()

        if (
            len(expected_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in expected_sha256
            )
        ):
            raise CommandError(
                "expected-sha256 must be a 64-character hex digest."
            )

        if not hmac.compare_digest(actual_sha256, expected_sha256):
            raise CommandError("Input SHA-256 does not match.")

        try:
            decoded = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CommandError(
                "Input file is not valid UTF-8."
            ) from exc

        try:
            payload = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise CommandError(
                f"Input file is not valid JSON: {exc}"
            ) from exc

        payload = _require_mapping(payload, "root payload")

        if _text(payload.get("schema_version")) != SCHEMA_VERSION:
            raise CommandError(
                f"schema_version must be {SCHEMA_VERSION}."
            )

        for key, expected_value in EXPECTED_SOURCE.items():
            actual_value = _text(payload.get(key))
            if actual_value != expected_value:
                raise CommandError(
                    f"{key} mismatch: expected {expected_value}."
                )

        _validate_media_policy(payload.get("media_policy"))

        profile_context = _normalize_context(
            payload.get("profile_context"),
            label="profile_context",
            expected_profile_id=EXPECTED_SOURCE[
                "source_profile_id"
            ],
        )
        customer_context = _normalize_context(
            payload.get("customer_context"),
            label="customer_context",
            expected_profile_id=EXPECTED_SOURCE[
                "source_customer_id"
            ],
            expected_user_id=EXPECTED_SOURCE[
                "source_customer_user_id"
            ],
        )
        profile_media = _normalize_media(
            payload.get("profile_media"),
            label="profile_media",
            expected_owner_user_id=EXPECTED_SOURCE[
                "source_profile_id"
            ],
        )
        customer_media = _normalize_media(
            payload.get("customer_media"),
            label="customer_media",
            expected_owner_user_id=EXPECTED_SOURCE[
                "source_customer_user_id"
            ],
        )
        data_quality = _normalize_data_quality(
            payload.get("data_quality")
        )

        thread = (
            ConversationThread.objects.filter(
                source_system=ConversationThread.SourceSystem.EUROTIKKEN,
                source_thread_id=EXPECTED_SOURCE[
                    "source_thread_id"
                ],
            )
            .select_related("creator", "channel")
            .first()
        )

        if thread is None:
            raise CommandError(
                "Existing Eurotikken ConversationThread was not found."
            )

        if thread.creator_id != options["creator_id"]:
            raise CommandError(
                "creator-id does not match the existing thread."
            )

        if thread.channel_id != options["channel_id"]:
            raise CommandError(
                "channel-id does not match the existing thread."
            )

        snapshot_exists = ConversationContextSnapshot.objects.filter(
            thread=thread
        ).exists()

        customer_reliability_warning = (
            customer_context["source_checked"] is False
        )

        if not options["apply"]:
            self.stdout.write("DRY RUN — no database changes.")
            self.stdout.write(
                f"source_thread_id={thread.source_thread_id}"
            )
            self.stdout.write(
                f"snapshot_exists={snapshot_exists}"
            )
            self.stdout.write(
                "would_create_context_snapshot="
                f"{not snapshot_exists}"
            )
            self.stdout.write(
                "would_update_context_snapshot="
                f"{snapshot_exists}"
            )
            self.stdout.write(
                f"profile_media_count={len(profile_media)}"
            )
            self.stdout.write(
                f"customer_media_count={len(customer_media)}"
            )
            self.stdout.write(
                "customer_source_checked="
                f"{customer_context['source_checked']}"
            )
            self.stdout.write(
                "customer_reliability_warning="
                f"{customer_reliability_warning}"
            )
            return

        defaults = {
            "schema_version": SCHEMA_VERSION,
            "source_sha256": actual_sha256,
            "profile_context": profile_context,
            "customer_context": customer_context,
            "profile_media": profile_media,
            "customer_media": customer_media,
            "data_quality": data_quality,
        }

        with transaction.atomic():
            _snapshot, created = (
                ConversationContextSnapshot.objects.update_or_create(
                    thread=thread,
                    defaults=defaults,
                )
            )

        self.stdout.write(
            "Applied Eurotikken operator context:"
        )
        self.stdout.write(f"snapshot_created={created}")
        self.stdout.write(f"snapshot_updated={not created}")
        self.stdout.write(
            f"profile_media_count={len(profile_media)}"
        )
        self.stdout.write(
            f"customer_media_count={len(customer_media)}"
        )
