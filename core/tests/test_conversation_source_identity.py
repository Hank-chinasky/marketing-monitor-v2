from django.test import TestCase

from core.models import ConversationMessage, ConversationThread, Creator, CreatorChannel
from core.services.chatties_identity import (
    build_chatties_message_source_id,
    build_chatties_thread_source_id,
)


class ConversationSourceIdentityTests(TestCase):
    def setUp(self):
        self.creator = Creator.objects.create(
            display_name="Source Identity Creator",
            legal_name="Source Identity Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="source-identity-channel",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
        )

    def test_thread_can_store_chatties_source_identity(self):
        source_thread_id = build_chatties_thread_source_id(12, 200, 100)

        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id=source_thread_id,
            source_site_id="12",
            source_site_label="chatties.nl",
            source_participant_a_id="100",
            source_participant_b_id="200",
            status=ConversationThread.Status.ACTIVE,
        )

        self.assertEqual(thread.source_system, ConversationThread.SourceSystem.CHATTIES)
        self.assertEqual(thread.source_thread_id, "chatties:12:100:200")
        self.assertEqual(thread.source_site_id, "12")
        self.assertEqual(thread.source_site_label, "chatties.nl")
        self.assertEqual(thread.source_participant_a_id, "100")
        self.assertEqual(thread.source_participant_b_id, "200")

    def test_message_can_store_chatties_source_identity(self):
        source_thread_id = build_chatties_thread_source_id(12, 200, 100)
        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id=source_thread_id,
            source_site_id="12",
            source_site_label="chatties.nl",
            source_participant_a_id="100",
            source_participant_b_id="200",
            status=ConversationThread.Status.ACTIVE,
        )

        message = ConversationMessage.objects.create(
            thread=thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Customer 100",
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_site_id="12",
            source_thread_id=source_thread_id,
            source_message_id=build_chatties_message_source_id(98765),
            source_sender_id="100",
            source_recipient_id="200",
            body="Hello from chatties.",
        )

        self.assertEqual(message.source_system, ConversationThread.SourceSystem.CHATTIES)
        self.assertEqual(message.source_site_id, "12")
        self.assertEqual(message.source_thread_id, "chatties:12:100:200")
        self.assertEqual(message.source_message_id, "chatties:messages:98765")
        self.assertEqual(message.source_sender_id, "100")
        self.assertEqual(message.source_recipient_id, "200")

    def test_existing_thread_without_optional_source_fields_remains_valid(self):
        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_thread_id="existing-thread",
            status=ConversationThread.Status.ACTIVE,
        )

        self.assertEqual(thread.source_system, ConversationThread.SourceSystem.MARA_CHAT)
        self.assertEqual(thread.source_thread_id, "existing-thread")
        self.assertEqual(thread.source_site_id, "")
        self.assertEqual(thread.source_site_label, "")
        self.assertEqual(thread.source_participant_a_id, "")
        self.assertEqual(thread.source_participant_b_id, "")

    def test_existing_message_without_source_fields_remains_valid(self):
        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_thread_id="message-thread",
            status=ConversationThread.Status.ACTIVE,
        )
        message = ConversationMessage.objects.create(
            thread=thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Customer",
            body="Hello from existing shape.",
        )

        self.assertEqual(message.source_system, "")
        self.assertEqual(message.source_site_id, "")
        self.assertEqual(message.source_thread_id, "")
        self.assertEqual(message.source_message_id, "")
        self.assertEqual(message.source_sender_id, "")
        self.assertEqual(message.source_recipient_id, "")
        self.assertEqual(message.body, "Hello from existing shape.")
        self.assertEqual(message.direction, ConversationMessage.Direction.INBOUND)

    def test_source_metadata_is_not_added_in_v1(self):
        self.assertFalse(hasattr(ConversationThread, "source_metadata"))
        self.assertFalse(hasattr(ConversationMessage, "source_metadata"))
        self.assertFalse(hasattr(CreatorChannel, "source_metadata"))

    def test_chatties_is_valid_thread_source_system_choice(self):
        self.assertIn(
            (ConversationThread.SourceSystem.CHATTIES, "Chatties"),
            ConversationThread.SourceSystem.choices,
        )

    def test_chatties_is_valid_message_source_system_choice(self):
        source_system_field = ConversationMessage._meta.get_field("source_system")
        self.assertIn(
            (ConversationThread.SourceSystem.CHATTIES, "Chatties"),
            source_system_field.choices,
        )

    def test_thread_uses_existing_source_thread_id_field_for_chatties(self):
        source_thread_field = ConversationThread._meta.get_field("source_thread_id")

        self.assertEqual(source_thread_field.max_length, 255)
        self.assertFalse(source_thread_field.blank)
        self.assertFalse(source_thread_field.null)

    def test_existing_thread_unique_constraint_name_remains_present(self):
        constraints = {
            constraint.name: constraint for constraint in ConversationThread._meta.constraints
        }

        self.assertIn("uniq_convthread_source_thread", constraints)
        self.assertEqual(
            tuple(constraints["uniq_convthread_source_thread"].fields),
            ("source_system", "source_thread_id"),
        )
