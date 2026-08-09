# Canonical product identity for legacy chat sources.
#
# The database still contains the historical ``mara_chat`` key for
# Eurotikken. This module keeps that storage detail separate from the
# product-facing source identity. It performs no writes or migrations.

CHATTIES_SOURCE = "chatties"
EUROTIKKEN_SOURCE = "eurotikken"
LEGACY_EUROTIKKEN_SOURCE = "mara_chat"

EUROTIKKEN_SOURCE_VALUES = (
    LEGACY_EUROTIKKEN_SOURCE,
    EUROTIKKEN_SOURCE,
)

SOURCE_LABELS = {
    CHATTIES_SOURCE: "Chatties",
    EUROTIKKEN_SOURCE: "Eurotikken",
}


def canonical_source_key(source_system: str) -> str:
    normalized = str(source_system or "").strip().lower()

    if normalized in EUROTIKKEN_SOURCE_VALUES:
        return EUROTIKKEN_SOURCE

    return normalized


def canonical_source_label(
    source_system: str,
    *,
    fallback: str = "",
) -> str:
    canonical_key = canonical_source_key(source_system)

    return (
        SOURCE_LABELS.get(canonical_key)
        or str(fallback or "").strip()
        or canonical_key
        or "Unknown source"
    )


def source_filter_values(source_filter: str) -> tuple[str, ...]:
    canonical_filter = canonical_source_key(source_filter)

    if canonical_filter == EUROTIKKEN_SOURCE:
        return EUROTIKKEN_SOURCE_VALUES

    if canonical_filter == CHATTIES_SOURCE:
        return (CHATTIES_SOURCE,)

    return ()
