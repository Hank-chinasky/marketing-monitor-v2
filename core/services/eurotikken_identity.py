def _normalize_numeric_source_id(value, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required.")

    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name} is required.")

    if not normalized.isdigit():
        raise ValueError(f"{field_name} must be numeric.")

    return str(int(normalized))


def build_eurotikken_thread_source_id(
    site_id,
    profile_id_a,
    profile_id_b,
) -> str:
    normalized_site_id = _normalize_numeric_source_id(
        site_id,
        "site_id",
    )
    normalized_profile_a = _normalize_numeric_source_id(
        profile_id_a,
        "profile_id_a",
    )
    normalized_profile_b = _normalize_numeric_source_id(
        profile_id_b,
        "profile_id_b",
    )

    participant_a, participant_b = sorted(
        [
            int(normalized_profile_a),
            int(normalized_profile_b),
        ]
    )

    return (
        f"eurotikken:{normalized_site_id}:"
        f"{participant_a}:{participant_b}"
    )


def build_eurotikken_message_source_id(message_id) -> str:
    normalized_message_id = _normalize_numeric_source_id(
        message_id,
        "message_id",
    )
    return f"eurotikken:messages:{normalized_message_id}"
