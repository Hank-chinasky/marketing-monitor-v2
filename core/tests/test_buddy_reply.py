from types import SimpleNamespace

from django.test import SimpleTestCase

from core.services.buddy_reply import build_operator_reply_draft


def message(direction, body):
    return SimpleNamespace(direction=direction, body=body)


class SuccessfulProvider:
    def __init__(self):
        self.context_packet = None

    def generate_reply(
        self,
        *,
        context_packet,
    ):
        self.context_packet = context_packet
        return {
            "draft_text": "Dit is een contextueel providerconcept.",
            "language": "nl",
            "source": "test-provider",
            "why_this_reply": "Het concept sluit aan op het laatste klantbericht.",
        }


class FailingProvider:
    def generate_reply(
        self,
        *,
        context_packet,
    ):
        raise RuntimeError("Provider unavailable")


class InvalidProvider:
    def generate_reply(
        self,
        *,
        context_packet,
    ):
        return {"draft_text": ""}


class BuddyReplyServiceTests(SimpleTestCase):
    def test_returns_empty_snapshot_without_selected_thread(self):
        result = build_operator_reply_draft(None, [])

        self.assertEqual(result["status"], "no_thread")
        self.assertEqual(result["reply_text"], "")
        self.assertEqual(result["latest_inbound_text"], "")
        self.assertEqual(result["language"], "unknown")
        self.assertEqual(result["source"], "no_thread")
        self.assertTrue(result["requires_human_review"])
        self.assertEqual(
            result["missing_context_note"],
            "Geen actieve thread geselecteerd.",
        )

    def test_provider_unavailable_does_not_fake_ai_reply(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hoi, kun je mij morgen helpen?"),
            ],
        )

        self.assertEqual(result["status"], "provider_unavailable")
        self.assertEqual(result["status_label"], "Nog geen Buddy-antwoord")
        self.assertEqual(result["language"], "nl")
        self.assertEqual(
            result["latest_inbound_text"],
            "Hoi, kun je mij morgen helpen?",
        )
        self.assertEqual(result["reply_text"], "")
        self.assertEqual(result["source"], "provider_unavailable")
        self.assertEqual(result["provider_error"], "")
        self.assertNotIn("Dankjewel voor je bericht", result["reply_text"])
        self.assertTrue(result["requires_human_review"])

    def test_existing_latest_draft_is_exposed_behind_same_boundary(self):
        latest_draft = SimpleNamespace(
            reply_text="Bestaand concept uit BuddyDraft."
        )

        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Olá, tudo bem?"),
            ],
            latest_draft=latest_draft,
        )

        self.assertEqual(result["status"], "existing_draft")
        self.assertEqual(
            result["latest_inbound_text"],
            "Olá, tudo bem?",
        )
        self.assertEqual(
            result["reply_text"],
            "Bestaand concept uit BuddyDraft.",
        )
        self.assertEqual(result["language"], "pt")
        self.assertEqual(result["source"], "latest_buddy_draft")
        self.assertEqual(result["provider_error"], "")
        self.assertTrue(result["requires_human_review"])

    def test_no_inbound_message_returns_no_reply_even_with_thread(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("outbound", "Operator update."),
            ],
        )

        self.assertEqual(result["status"], "no_inbound_message")
        self.assertEqual(result["reply_text"], "")
        self.assertEqual(result["latest_inbound_text"], "")
        self.assertEqual(result["language"], "unknown")
        self.assertEqual(result["source"], "no_inbound_message")
        self.assertEqual(
            result["missing_context_note"],
            "Geen inkomend klantbericht beschikbaar.",
        )

    def test_latest_inbound_message_controls_visible_context(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hoi, kun je mij helpen?"),
                message("outbound", "Eerdere operatorreactie."),
                message("inbound", "Hello, can you help me today?"),
            ],
        )

        self.assertEqual(result["language"], "en")
        self.assertEqual(
            result["latest_inbound_text"],
            "Hello, can you help me today?",
        )
        self.assertEqual(result["status"], "provider_unavailable")
        self.assertEqual(result["reply_text"], "")

    def test_successful_provider_returns_structured_ready_state(self):
        provider = SuccessfulProvider()

        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hoi, kun je mij morgen helpen?"),
            ],
            buddy_context={
                "thread_summary": "Warme lopende follow-up.",
                "profile_tone": "Speels en vertrouwd.",
                "open_loop": "Pak de laatste vraag op.",
                "do_not_do": "Niet generiek openen.",
                "recommended_next_action": (
                    "Ga door op de bestaande gesprekstrant."
                ),
                "reliability_label": "Hoog",
                "reliability_reason": "Kerncontext is aanwezig.",
                "missing_context": [],
            },
            provider=provider,
        )

        self.assertEqual(result["status"], "ready")
        self.assertIsNotNone(provider.context_packet)
        self.assertEqual(
            provider.context_packet["schema_version"],
            "buddy-context-v1",
        )
        self.assertEqual(
            provider.context_packet["latest_inbound_text"],
            "Hoi, kun je mij morgen helpen?",
        )
        self.assertEqual(
            provider.context_packet["do_not_do"],
            "Niet generiek openen.",
        )
        self.assertNotIn("selected_thread", provider.context_packet)
        self.assertNotIn("conversation_messages", provider.context_packet)
        self.assertNotIn("operator", provider.context_packet)
        self.assertEqual(
            result["reply_text"],
            "Dit is een contextueel providerconcept.",
        )
        self.assertEqual(result["language"], "nl")
        self.assertEqual(result["source"], "test-provider")
        self.assertEqual(result["provider_error"], "")
        self.assertIn(
            "laatste klantbericht",
            result["tone_note"],
        )
        self.assertTrue(result["requires_human_review"])

    def test_provider_exception_becomes_explicit_error_state(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hello, can you help me today?"),
            ],
            provider=FailingProvider(),
        )

        self.assertEqual(result["status"], "provider_error")
        self.assertEqual(result["reply_text"], "")
        self.assertIn(
            "geen geldig concept",
            result["provider_error"],
        )
        self.assertTrue(
            result["source"].startswith("provider_error:")
        )

    def test_invalid_provider_payload_becomes_explicit_error_state(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hello, can you help me today?"),
            ],
            provider=InvalidProvider(),
        )

        self.assertEqual(result["status"], "provider_error")
        self.assertEqual(result["reply_text"], "")
        self.assertNotEqual(result["provider_error"], "")

    def test_returned_dict_contains_reply_focus_contract_fields(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hello, can you help me today?"),
            ],
        )

        expected_fields = {
            "status",
            "status_label",
            "status_badge",
            "latest_inbound_text",
            "reply_text",
            "language",
            "source",
            "provider_error",
            "requires_human_review",
            "safety_note",
            "missing_context_note",
            "tone_note",
        }

        self.assertTrue(expected_fields.issubset(result.keys()))
