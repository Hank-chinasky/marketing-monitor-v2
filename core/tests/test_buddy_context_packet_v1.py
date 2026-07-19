from datetime import datetime, timezone
import json
from types import SimpleNamespace

from django.test import SimpleTestCase

from core.services.buddy_context import build_buddy_context_packet


def message(
    direction,
    body,
    *,
    source_system="chatties",
    occurred_at=None,
):
    return SimpleNamespace(
        direction=direction,
        body=body,
        source_system=source_system,
        occurred_at=occurred_at
        or datetime(
            2026,
            7,
            19,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        sender_label="Niet nodig",
        source_message_id="sensitive-message-id",
        source_sender_id="sensitive-sender-id",
        source_recipient_id="sensitive-recipient-id",
    )


def thread():
    return SimpleNamespace(
        status="waiting_on_operator",
        source_system="chatties",
        source_site_label="Chatties NL",
        source_thread_id="sensitive-thread-id",
        source_participant_a_id="sensitive-a",
        source_participant_b_id="sensitive-b",
        thread_summary="Warme lopende follow-up.",
        open_loop="Pak de laatste persoonlijke vraag op.",
        last_approved_reply_style="Warm, speels en vertrouwd.",
        channel=SimpleNamespace(
            handle="Verpleegstertje",
            profile_url="https://secret.example/profile",
            access_notes="geheime toegangsinformatie",
            access_profile_notes="meer geheime toegangsinformatie",
            account_email="secret@example.com",
            account_phone_number="+31 6 12345678",
        ),
        creator=SimpleNamespace(
            display_name="Demo-profiel",
        ),
    )


class BuddyContextPacketV1Tests(SimpleTestCase):
    def test_packet_limits_recent_messages_and_excludes_internal_notes(self):
        messages = [
            message("inbound", f"Bericht {number}")
            for number in range(1, 11)
        ]
        messages.append(
            message(
                "internal_note",
                "Deze interne notitie mag nooit naar de provider.",
            )
        )

        packet = build_buddy_context_packet(
            thread(),
            messages,
            language="nl",
        )

        self.assertEqual(packet["schema_version"], "buddy-context-v1")
        self.assertEqual(len(packet["recent_messages"]), 8)
        self.assertEqual(
            packet["recent_messages"][0]["body"],
            "Bericht 3",
        )
        self.assertEqual(
            packet["recent_messages"][-1]["body"],
            "Bericht 10",
        )
        self.assertEqual(
            packet["latest_inbound_text"],
            "Bericht 10",
        )

        serialized = json.dumps(packet)

        self.assertNotIn("interne notitie", serialized.lower())
        self.assertNotIn("sensitive-message-id", serialized)
        self.assertNotIn("sensitive-sender-id", serialized)

    def test_packet_enforces_hard_maximum_for_requested_limit(self):
        messages = [
            message("inbound", f"Bericht {number}")
            for number in range(1, 13)
        ]

        packet = build_buddy_context_packet(
            thread(),
            messages,
            language="nl",
            recent_message_limit=99,
        )

        self.assertEqual(len(packet["recent_messages"]), 8)
        self.assertEqual(
            packet["recent_messages"][0]["body"],
            "Bericht 5",
        )
        self.assertEqual(
            packet["recent_messages"][-1]["body"],
            "Bericht 12",
        )

    def test_packet_reuses_existing_buddy_assist_context(self):
        buddy_assist = {
            "thread_summary": "Samenvatting vanuit Buddy Surface.",
            "profile_tone": "Plagerig en vertrouwd.",
            "open_loop": "Vraag door op zijn werkroute.",
            "do_not_do": "Niet resetten en niet generiek openen.",
            "recommended_next_action": "Pak de werkroute weer op.",
            "reliability_label": "Hoog",
            "reliability_reason": "Kerncontext is aanwezig.",
            "missing_context": [],
        }

        packet = build_buddy_context_packet(
            thread(),
            [message("inbound", "Hoe was je dag?")],
            buddy_assist=buddy_assist,
            language="nl",
        )

        self.assertEqual(
            packet["thread_summary"],
            "Samenvatting vanuit Buddy Surface.",
        )
        self.assertEqual(
            packet["profile_tone"],
            "Plagerig en vertrouwd.",
        )
        self.assertEqual(
            packet["do_not_do"],
            "Niet resetten en niet generiek openen.",
        )
        self.assertEqual(
            packet["recommended_next_action"],
            "Pak de werkroute weer op.",
        )
        self.assertEqual(
            packet["reliability"]["label"],
            "Hoog",
        )

    def test_packet_masks_recognizable_email_and_phone_data(self):
        packet = build_buddy_context_packet(
            thread(),
            [
                message(
                    "inbound",
                    (
                        "Afspraak 19-07-2026. "
                        "Mail jan@example.com of bel +31 6 12345678."
                    ),
                )
            ],
            buddy_assist={
                "thread_summary": (
                    "Alternatief test@example.org of 0612345678."
                ),
            },
            language="nl",
        )

        serialized = json.dumps(packet)

        self.assertNotIn("jan@example.com", serialized)
        self.assertNotIn("test@example.org", serialized)
        self.assertNotIn("0612345678", serialized)
        self.assertNotIn("+31 6 12345678", serialized)
        self.assertIn("[email]", serialized)
        self.assertIn("[phone]", serialized)
        self.assertIn("19-07-2026", serialized)

    def test_packet_masks_sensitive_source_labels(self):
        selected_thread = thread()
        selected_thread.source_site_label = "owner@example.com"
        selected_thread.channel.handle = "+31 6 12345678"

        packet = build_buddy_context_packet(
            selected_thread,
            [message("inbound", "Laatste klantbericht.")],
            language="nl",
        )

        self.assertEqual(packet["source_account"], "[email]")
        self.assertEqual(packet["profile_name"], "[phone]")

    def test_packet_excludes_operational_and_source_identifiers(self):
        packet = build_buddy_context_packet(
            thread(),
            [message("inbound", "Laatste klantbericht.")],
            language="nl",
        )

        serialized = json.dumps(packet)

        self.assertEqual(
            packet["source_platform"],
            "chatties",
        )
        self.assertEqual(
            packet["source_account"],
            "Chatties NL",
        )
        self.assertEqual(
            packet["profile_name"],
            "Verpleegstertje",
        )

        self.assertNotIn("sensitive-thread-id", serialized)
        self.assertNotIn("sensitive-a", serialized)
        self.assertNotIn("sensitive-b", serialized)
        self.assertNotIn("secret.example", serialized)
        self.assertNotIn("geheime toegangsinformatie", serialized)
        self.assertNotIn("secret@example.com", serialized)
