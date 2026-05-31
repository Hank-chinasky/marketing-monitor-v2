from types import SimpleNamespace

from django.test import SimpleTestCase

from core.services.buddy_reply import build_operator_reply_draft


def message(direction, body):
    return SimpleNamespace(direction=direction, body=body)


class BuddyReplyServiceTests(SimpleTestCase):
    def test_returns_empty_snapshot_without_selected_thread(self):
        result = build_operator_reply_draft(None, [])

        self.assertEqual(result["reply_text"], "")
        self.assertEqual(result["language"], "unknown")
        self.assertEqual(result["source"], "no_thread")
        self.assertTrue(result["requires_human_review"])
        self.assertEqual(result["missing_context_note"], "No active thread selected.")
        self.assertEqual(
            result["tone_note"],
            "No draft should be used until thread context is available.",
        )

    def test_builds_dutch_quality_reply_from_latest_inbound_message(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hoi, kun je mij morgen helpen?"),
                message("outbound", "Eerdere reactie."),
            ],
        )

        self.assertEqual(result["language"], "nl")
        self.assertEqual(result["source"], "deterministic_quality_v1")
        self.assertIn("Dankjewel voor je bericht", result["reply_text"])
        self.assertEqual(result["missing_context_note"], "")
        self.assertIn("short, careful", result["tone_note"])
        self.assertTrue(result["requires_human_review"])

    def test_builds_german_quality_reply_from_latest_inbound_message(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hallo, kannst du meine Frage heute beantworten?"),
            ],
        )

        self.assertEqual(result["language"], "de")
        self.assertEqual(result["source"], "deterministic_quality_v1")
        self.assertIn("Danke für deine Nachricht", result["reply_text"])
        self.assertTrue(result["requires_human_review"])

    def test_builds_english_quality_reply_from_latest_inbound_message(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hello, can you help me today?"),
            ],
        )

        self.assertEqual(result["language"], "en")
        self.assertEqual(result["source"], "deterministic_quality_v1")
        self.assertIn("Thanks for your message", result["reply_text"])
        self.assertTrue(result["requires_human_review"])

    def test_builds_portuguese_quality_reply_from_latest_inbound_message(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Olá, tudo bem? Pode responder por favor?"),
            ],
        )

        self.assertEqual(result["language"], "pt")
        self.assertEqual(result["source"], "deterministic_quality_v1")
        self.assertIn("Obrigado pela mensagem", result["reply_text"])
        self.assertTrue(result["requires_human_review"])

    def test_latest_inbound_message_controls_language(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message("inbound", "Hoi, kun je mij helpen?"),
                message("inbound", "Hello, can you help me today?"),
            ],
        )

        self.assertEqual(result["language"], "en")
        self.assertIn("Thanks for your message", result["reply_text"])

    def test_existing_latest_draft_is_exposed_read_only_behind_same_boundary(self):
        latest_draft = SimpleNamespace(reply_text="Bestaand concept uit BuddyDraft.")
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[message("inbound", "Olá, tudo bem?")],
            latest_draft=latest_draft,
        )

        self.assertEqual(result["reply_text"], "Bestaand concept uit BuddyDraft.")
        self.assertEqual(result["language"], "pt")
        self.assertEqual(result["source"], "latest_buddy_draft")
        self.assertEqual(result["missing_context_note"], "")
        self.assertIn("Review the existing draft", result["tone_note"])
        self.assertTrue(result["requires_human_review"])

    def test_no_inbound_message_returns_no_draft_text(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[message("outbound", "Operator update.")],
        )

        self.assertEqual(result["reply_text"], "")
        self.assertEqual(result["language"], "unknown")
        self.assertEqual(result["source"], "no_inbound_message")
        self.assertEqual(
            result["missing_context_note"],
            "No inbound customer message is available.",
        )
        self.assertEqual(
            result["tone_note"],
            "Wait for customer context before drafting a reply.",
        )
        self.assertTrue(result["requires_human_review"])

    def test_returned_dict_contains_quality_notes(self):
        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[message("inbound", "Hello, can you help me today?")],
        )

        self.assertIn("missing_context_note", result)
        self.assertIn("tone_note", result)
        self.assertIn("safety_note", result)
        self.assertTrue(result["requires_human_review"])
