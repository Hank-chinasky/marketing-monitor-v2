from django.test import SimpleTestCase

from core.services.chatties_identity import (
    build_chatties_message_source_id,
    build_chatties_thread_source_id,
)


class ChattiesIdentityTests(SimpleTestCase):
    def test_thread_source_id_normalizes_participant_order(self):
        self.assertEqual(
            build_chatties_thread_source_id(12, 200, 100),
            "chatties:12:100:200",
        )

    def test_thread_source_id_separates_different_web_ids(self):
        self.assertNotEqual(
            build_chatties_thread_source_id(12, 100, 200),
            build_chatties_thread_source_id(13, 100, 200),
        )

    def test_thread_source_id_accepts_int_and_numeric_string_input(self):
        self.assertEqual(
            build_chatties_thread_source_id("12", "200", 100),
            "chatties:12:100:200",
        )

    def test_thread_source_id_rejects_empty_web_id(self):
        with self.assertRaises(ValueError):
            build_chatties_thread_source_id("", 100, 200)

    def test_thread_source_id_rejects_none_web_id(self):
        with self.assertRaises(ValueError):
            build_chatties_thread_source_id(None, 100, 200)

    def test_thread_source_id_rejects_empty_participant_ids(self):
        with self.assertRaises(ValueError):
            build_chatties_thread_source_id(12, "", 200)

        with self.assertRaises(ValueError):
            build_chatties_thread_source_id(12, 100, "")

    def test_thread_source_id_rejects_none_participant_ids(self):
        with self.assertRaises(ValueError):
            build_chatties_thread_source_id(12, None, 200)

        with self.assertRaises(ValueError):
            build_chatties_thread_source_id(12, 100, None)

    def test_thread_source_id_rejects_non_numeric_ids(self):
        with self.assertRaises(ValueError):
            build_chatties_thread_source_id("site", 100, 200)

        with self.assertRaises(ValueError):
            build_chatties_thread_source_id(12, "profile-a", 200)

        with self.assertRaises(ValueError):
            build_chatties_thread_source_id(12, 100, "profile-b")

    def test_thread_source_id_sorts_participants_numerically(self):
        self.assertEqual(
            build_chatties_thread_source_id(12, 2, 10),
            "chatties:12:2:10",
        )

    def test_message_source_id_is_deterministic(self):
        self.assertEqual(
            build_chatties_message_source_id(98765),
            "chatties:messages:98765",
        )

    def test_message_source_id_accepts_int_and_numeric_string_input(self):
        self.assertEqual(
            build_chatties_message_source_id("98765"),
            "chatties:messages:98765",
        )

    def test_message_source_id_rejects_empty_message_id(self):
        with self.assertRaises(ValueError):
            build_chatties_message_source_id("")

    def test_message_source_id_rejects_none_message_id(self):
        with self.assertRaises(ValueError):
            build_chatties_message_source_id(None)

    def test_message_source_id_rejects_non_numeric_message_id(self):
        with self.assertRaises(ValueError):
            build_chatties_message_source_id("message-id")
