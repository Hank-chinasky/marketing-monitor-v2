from django.test import SimpleTestCase, override_settings

from core.services.buddy_provider import (
    get_configured_buddy_provider,
)


class ValidProvider:
    def generate_reply(
        self,
        *,
        context_packet,
    ):
        return {
            "draft_text": "Veilig testconcept.",
            "language": "nl",
            "refusal_status": "none",
        }


class InvalidProvider:
    pass


class BuddyProviderRouterV1Tests(SimpleTestCase):
    @override_settings(BUDDY_REPLY_PROVIDER="")
    def test_provider_is_disabled_by_default(self):
        provider = get_configured_buddy_provider(
            factories={
                "test": ValidProvider,
            }
        )

        self.assertIsNone(provider)

    @override_settings(BUDDY_REPLY_PROVIDER="unknown")
    def test_unknown_configured_provider_fails_closed(self):
        provider = get_configured_buddy_provider(
            factories={
                "test": ValidProvider,
            }
        )

        self.assertIsNone(provider)

    def test_explicit_provider_name_is_normalized(self):
        provider = get_configured_buddy_provider(
            provider_name="  TEST  ",
            factories={
                "test": ValidProvider,
            },
        )

        self.assertIsInstance(provider, ValidProvider)

    def test_non_callable_factory_fails_closed(self):
        provider = get_configured_buddy_provider(
            provider_name="broken",
            factories={
                "broken": object(),
            },
        )

        self.assertIsNone(provider)

    def test_factory_exception_fails_closed(self):
        def failing_factory():
            raise RuntimeError("Initialization failed")

        provider = get_configured_buddy_provider(
            provider_name="broken",
            factories={
                "broken": failing_factory,
            },
        )

        self.assertIsNone(provider)

    def test_factory_returning_none_fails_closed(self):
        provider = get_configured_buddy_provider(
            provider_name="empty",
            factories={
                "empty": lambda: None,
            },
        )

        self.assertIsNone(provider)

    def test_object_without_generate_reply_fails_closed(self):
        provider = get_configured_buddy_provider(
            provider_name="invalid",
            factories={
                "invalid": InvalidProvider,
            },
        )

        self.assertIsNone(provider)

    @override_settings(BUDDY_REPLY_PROVIDER="test")
    def test_django_setting_selects_registered_factory(self):
        provider = get_configured_buddy_provider(
            factories={
                "test": ValidProvider,
            }
        )

        self.assertIsInstance(provider, ValidProvider)
