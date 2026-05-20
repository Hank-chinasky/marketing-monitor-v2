from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models import ConversationMessage, ConversationThread, Creator, CreatorChannel


class ConversationThreadModelTests(TestCase):
    def setUp(self):
        self.creator = Creator.objects.create(
            display_name="Creator One",
            legal_name="Creator One BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="creator-one",
            profile_url="https://instagram.com/creator-one",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.CREATOR,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
        )

    def test_conversation_thread_crud_works(self):
        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="mara-thread-001",
            status=ConversationThread.Status.ACTIVE,
            last_message_at=timezone.now(),
            thread_summary="Customer asks about pricing.",
            open_loop="Need operator answer.",
            guardrails="No promises about delivery date.",
            risk_flags="pricing_question",
            last_handoff_note="Check pricing table before replying.",
            last_approved_reply_style="calm and concise",
            active=True,
        )

        self.assertEqual(thread.creator, self.creator)
        self.assertEqual(thread.channel, self.channel)
        self.assertEqual(thread.source_system, ConversationThread.SourceSystem.MARA_CHAT)
        self.assertEqual(thread.status, ConversationThread.Status.ACTIVE)
        self.assertEqual(thread.thread_summary, "Customer asks about pricing.")
        self.assertTrue(thread.active)

        thread.status = ConversationThread.Status.WAITING_ON_OPERATOR
        thread.open_loop = "Operator still needs to approve."
        thread.save(update_fields=["status", "open_loop", "updated_at"])

        thread.refresh_from_db()
        self.assertEqual(thread.status, ConversationThread.Status.WAITING_ON_OPERATOR)
        self.assertEqual(thread.open_loop, "Operator still needs to approve.")

    def test_unique_constraint_on_source_system_and_source_thread_id(self):
        ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="duplicate-thread",
        )

        with self.assertRaises(IntegrityError):
            ConversationThread.objects.create(
                creator=self.creator,
                channel=self.channel,
                source_system=ConversationThread.SourceSystem.MARA_CHAT,
                source_thread_id="duplicate-thread",
            )

    def test_source_system_choices_validate(self):
        thread = ConversationThread(
            creator=self.creator,
            channel=self.channel,
            source_system="other_chat",
            source_thread_id="thread-invalid-source",
            status=ConversationThread.Status.ACTIVE,
        )

        with self.assertRaises(ValidationError) as exc:
            thread.full_clean()

        self.assertIn("source_system", exc.exception.message_dict)

    def test_status_choices_validate(self):
        thread = ConversationThread(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="thread-invalid-status",
            status="realtime",
        )

        with self.assertRaises(ValidationError) as exc:
            thread.full_clean()

        self.assertIn("status", exc.exception.message_dict)

    def test_channel_is_nullable(self):
        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=None,
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="thread-without-channel",
            status=ConversationThread.Status.HANDOFF_REQUIRED,
        )

        self.assertIsNone(thread.channel)
        self.assertEqual(thread.creator, self.creator)

    def test_creator_is_required_scope_anchor(self):
        thread = ConversationThread(
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="missing-creator",
            status=ConversationThread.Status.ACTIVE,
        )

        with self.assertRaises(ValidationError) as exc:
            thread.full_clean()

        self.assertIn("creator", exc.exception.message_dict)

    def test_conversation_message_crud_defaults_and_required_body(self):
        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="thread-with-message",
            status=ConversationThread.Status.ACTIVE,
        )

        before = timezone.now()
        message = ConversationMessage.objects.create(
            thread=thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Customer",
            source_message_id="source-msg-001",
            body="Hallo, ik heb een vraag.",
        )

        self.assertEqual(message.thread, thread)
        self.assertEqual(message.direction, ConversationMessage.Direction.INBOUND)
        self.assertEqual(message.body, "Hallo, ik heb een vraag.")
        self.assertGreaterEqual(message.occurred_at, before)
        self.assertIsNotNone(message.created_at)

        invalid_message = ConversationMessage(
            thread=thread,
            direction=ConversationMessage.Direction.INBOUND,
            body="",
        )
        with self.assertRaises(ValidationError) as exc:
            invalid_message.full_clean()

        self.assertIn("body", exc.exception.message_dict)

    def test_conversation_message_direction_choices_validate(self):
        thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="thread-with-invalid-message-direction",
            status=ConversationThread.Status.ACTIVE,
        )
        message = ConversationMessage(
            thread=thread,
            direction="external_sync",
            body="Message body.",
        )

        with self.assertRaises(ValidationError) as exc:
            message.full_clean()

        self.assertIn("direction", exc.exception.message_dict)
