from django.test import TestCase

from core.models import (
    ConversationMessage,
    ConversationThread,
    Creator,
    CreatorChannel,
)
from core.services.eurotikken_identity import (
    build_eurotikken_message_source_id,
    build_eurotikken_thread_source_id,
)


class EurotikkenSourceIdentityTests(TestCase):
    def setUp(self):
        self.creator = Creator.objects.create(
            display_name="Eurotikken Source Creator",
            legal_name="Eurotikken Source Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="datesamen-source",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
        )

    def test_build_thread_source_id_sorts_participants(self):
        self.assertEqual(
            build_eurotikken_thread_source_id(25, 60010, 2390),
            "eurotikken:25:2390:60010",
        )

    def test_build_message_source_id(self):
        self.assertEqual(
            build_eurotikken_message_source_id(5191815),
            "eurotikken:messages:5191815",
        )

    def test_identity_rejects_missing_or_non_numeric_values(self):
        invalid_calls = [
            lambda: build_eurotikken_thread_source_id(None, 2390, 60010),
            lambda: build_eurotikken_thread_source_id(25, "", 60010),
            lambda: build_eurotikken_thread_source_id(25, 2390, "customer"),
            lambda: build_eurotikken_message_source_id("message"),
        ]

        for invalid_call in invalid_calls:
            with self.subTest(invalid_call=invalid_call):
                with self.assertRaises(ValueError):
                    invalid_call()

    def test_thread_can_store_eurotikken_source_identity(self):
        source_thread_id = build_eurotikken_thread_source_id(
            25,
            2390,
            60010,
        )

        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.EUROTIKKEN,
            source_thread_id=source_thread_id,
            source_site_id="25",
            source_site_label="datesamen.nl",
            source_participant_a_id="2390",
            source_participant_b_id="60010",
            status=ConversationThread.Status.ACTIVE,
        )

        self.assertEqual(
            thread.source_system,
            ConversationThread.SourceSystem.EUROTIKKEN,
        )
        self.assertEqual(
            thread.source_thread_id,
            "eurotikken:25:2390:60010",
        )
        self.assertEqual(thread.source_site_id, "25")
        self.assertEqual(thread.source_site_label, "datesamen.nl")
        self.assertEqual(thread.source_participant_a_id, "2390")
        self.assertEqual(thread.source_participant_b_id, "60010")

    def test_message_can_store_eurotikken_source_identity(self):
        source_thread_id = build_eurotikken_thread_source_id(
            25,
            2390,
            60010,
        )

        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.EUROTIKKEN,
            source_thread_id=source_thread_id,
            source_site_id="25",
            source_site_label="datesamen.nl",
            source_participant_a_id="2390",
            source_participant_b_id="60010",
            status=ConversationThread.Status.ACTIVE,
        )

        message = ConversationMessage.objects.create(
            thread=thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Eurotikken customer 60010",
            source_system=ConversationThread.SourceSystem.EUROTIKKEN,
            source_site_id="25",
            source_thread_id=source_thread_id,
            source_message_id=build_eurotikken_message_source_id(
                5191813
            ),
            source_sender_id="60010",
            source_recipient_id="2390",
            body="Synthetic Eurotikken test message.",
        )

        self.assertEqual(
            message.source_system,
            ConversationThread.SourceSystem.EUROTIKKEN,
        )
        self.assertEqual(
            message.source_thread_id,
            "eurotikken:25:2390:60010",
        )
        self.assertEqual(
            message.source_message_id,
            "eurotikken:messages:5191813",
        )
        self.assertEqual(message.source_sender_id, "60010")
        self.assertEqual(message.source_recipient_id, "2390")

    def test_eurotikken_is_valid_source_system_choice(self):
        expected_choice = (
            ConversationThread.SourceSystem.EUROTIKKEN,
            "Eurotikken",
        )

        self.assertIn(
            expected_choice,
            ConversationThread.SourceSystem.choices,
        )

        message_field = ConversationMessage._meta.get_field(
            "source_system"
        )
        self.assertIn(expected_choice, message_field.choices)
