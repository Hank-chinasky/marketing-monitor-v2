import os
from collections.abc import Callable, Mapping
from typing import Any

from django.conf import settings

from core.services.buddy_reply import BuddyReplyProvider


BuddyProviderFactory = Callable[[], BuddyReplyProvider]


def _build_venice_provider() -> BuddyReplyProvider:
    from core.services.buddy_venice import (
        build_venice_provider_from_environment,
    )

    return build_venice_provider_from_environment()


# Providers worden uitsluitend via expliciete aliases geregistreerd.
# Configuratie kan nooit een willekeurig Python-pad importeren.
PROVIDER_FACTORIES: dict[str, BuddyProviderFactory] = {
    "venice": _build_venice_provider,
}


def _provider_name(value: Any) -> str:
    return str(value or "").strip().lower()


def _configured_provider_name(
    explicit_provider_name: Any,
) -> str:
    if explicit_provider_name is not None:
        return _provider_name(explicit_provider_name)

    settings_value = getattr(
        settings,
        "BUDDY_REPLY_PROVIDER",
        "",
    )
    settings_name = _provider_name(settings_value)

    if settings_name:
        return settings_name

    return _provider_name(
        os.getenv("BUDDY_REPLY_PROVIDER", "")
    )


def get_configured_buddy_provider(
    *,
    provider_name: Any = None,
    factories: Mapping[str, Any] | None = None,
) -> BuddyReplyProvider | None:
    """Return one configured provider instance or fail closed with None.

    Unknown names, invalid factories, missing credentials and provider
    initialization failures all resolve to None.
    """

    configured_name = _configured_provider_name(
        provider_name
    )

    if not configured_name:
        return None

    registry = (
        PROVIDER_FACTORIES
        if factories is None
        else factories
    )
    factory = registry.get(configured_name)

    if not callable(factory):
        return None

    try:
        provider = factory()
    except Exception:
        return None

    if provider is None:
        return None

    if not callable(
        getattr(provider, "generate_reply", None)
    ):
        return None

    return provider
