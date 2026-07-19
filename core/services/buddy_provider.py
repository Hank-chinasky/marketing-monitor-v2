from collections.abc import Callable, Mapping
from typing import Any

from django.conf import settings

from core.services.buddy_reply import BuddyReplyProvider


BuddyProviderFactory = Callable[[], BuddyReplyProvider]

# Providers worden uitsluitend via expliciete aliases geregistreerd.
# Een setting kan dus nooit een willekeurig Python-pad importeren.
PROVIDER_FACTORIES: dict[str, BuddyProviderFactory] = {}


def _provider_name(value: Any) -> str:
    return str(value or "").strip().lower()


def get_configured_buddy_provider(
    *,
    provider_name: Any = None,
    factories: Mapping[str, Any] | None = None,
) -> BuddyReplyProvider | None:
    """Return one configured provider instance or fail closed with None.

    This router performs no network calls and reads no credentials.
    Unknown names, invalid factories and initialization failures all
    resolve to None so the reply service retains its honest unavailable state.
    """

    configured_name = _provider_name(
        getattr(settings, "BUDDY_REPLY_PROVIDER", "")
        if provider_name is None
        else provider_name
    )

    if not configured_name:
        return None

    registry = PROVIDER_FACTORIES if factories is None else factories
    factory = registry.get(configured_name)

    if not callable(factory):
        return None

    try:
        provider = factory()
    except Exception:
        return None

    if provider is None:
        return None

    if not callable(getattr(provider, "generate_reply", None)):
        return None

    return provider
