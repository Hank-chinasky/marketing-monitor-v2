from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urljoin, urlsplit

from django.core.exceptions import ObjectDoesNotExist


SOURCE_MEDIA_BASE_URLS = {
    ("eurotikken", "25"): "https://datesamen.nl/media/",
}

ALLOWED_MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_age(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if not 18 <= value <= 130:
        return None
    return value


def _compact_context(
    value: Any,
    *,
    include_profile_fields: bool,
) -> dict[str, Any]:
    raw = value if isinstance(value, dict) else {}

    result = {
        "display_name": _text(raw.get("display_name")),
        "age": _safe_age(raw.get("age")),
        "city": _text(raw.get("city")),
        "region": _text(raw.get("region")),
        "country": _text(raw.get("country")),
        "marital_status": _text(raw.get("marital_status")),
        "goal": _text(raw.get("goal")),
        "source_checked": raw.get("source_checked") is True,
        "source_reviewed": raw.get("source_reviewed") is True,
    }

    if include_profile_fields:
        result.update(
            {
                "occupation": _text(raw.get("occupation")),
                "summary": _text(raw.get("summary")),
            }
        )

    return result


def _safe_relative_media_path(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    source_path = value.strip()

    if (
        not source_path
        or not source_path.startswith("uploaded_files/")
        or source_path.startswith("/")
        or "\\" in source_path
        or "%" in source_path
        or "//" in source_path
    ):
        return ""

    parsed = urlsplit(source_path)
    if (
        parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or parsed.path != source_path
    ):
        return ""

    parts = PurePosixPath(source_path).parts
    if (
        len(parts) < 2
        or ".." in parts
        or "." in parts
        or PurePosixPath(source_path).suffix.lower()
        not in ALLOWED_MEDIA_EXTENSIONS
    ):
        return ""

    return source_path


def _build_customer_media(
    raw_media: Any,
    *,
    source_system: str,
    source_site_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(raw_media, list):
        return []

    base_url = SOURCE_MEDIA_BASE_URLS.get(
        (source_system, source_site_id)
    )
    if not base_url:
        return []

    result = []

    for raw_item in raw_media[:10]:
        if not isinstance(raw_item, dict):
            continue
        if raw_item.get("media_type") != "image":
            continue
        if raw_item.get("allow_external_ai") is not False:
            continue
        if raw_item.get("requires_operator_reveal") is not True:
            continue
        if raw_item.get("default_visibility") != "covered":
            continue
        if raw_item.get("active") is False:
            continue

        source_media_id = _text(
            raw_item.get("source_media_id")
        )
        if not source_media_id.isdigit():
            continue

        source_path = _safe_relative_media_path(
            raw_item.get("source_path")
        )
        if not source_path:
            continue

        result.append(
            {
                "source_media_id": source_media_id,
                "reveal_url": urljoin(base_url, source_path),
                "is_primary": (
                    raw_item.get("is_primary") is True
                ),
            }
        )

    return result


def build_operator_context(thread: Any) -> dict[str, Any]:
    empty = {
        "available": False,
        "profile": {},
        "customer": {},
        "customer_media": [],
        "customer_reliability_warning": False,
        "customer_review_missing": False,
    }

    if thread is None:
        return empty

    try:
        snapshot = thread.context_snapshot
    except (AttributeError, ObjectDoesNotExist):
        return empty

    # Een reeds geladen OneToOne-relatie kan na delete nog in Django's
    # instance-cache staan. Een snapshot zonder primaire sleutel bestaat
    # niet meer en mag daarom niet als beschikbare context gelden.
    if getattr(snapshot, "pk", None) is None:
        return empty

    profile = _compact_context(
        snapshot.profile_context,
        include_profile_fields=True,
    )
    customer = _compact_context(
        snapshot.customer_context,
        include_profile_fields=False,
    )

    source_system = _text(
        getattr(thread, "source_system", "")
    )
    source_site_id = _text(
        getattr(thread, "source_site_id", "")
    )

    return {
        "available": True,
        "profile": profile,
        "customer": customer,
        "customer_media": _build_customer_media(
            snapshot.customer_media,
            source_system=source_system,
            source_site_id=source_site_id,
        ),
        "customer_reliability_warning": (
            customer["source_reviewed"] is True
            and customer["source_checked"] is False
        ),
        "customer_review_missing": (
            customer["source_reviewed"] is False
        ),
    }
