import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from core.models import (
    ConversationMessage,
    ConversationThread,
    Creator,
    CreatorChannel,
)


class ImportEurotikkenThreadCommandTests(TestCase):
    def setUp(self):
        self.creator = Creator.objects.create(
            display_name="Sonja",
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="eurotikken:datesamen.nl:2390",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.DRAFT_ONLY,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
        )

    def _payload(self):
        return {
            "schema_version": "eurotikken-thread-export-v1",
            "source_system": "eurotikken",
            "source_site_id": "25",
            "source_site_label": "datesamen.nl",
            "source_profile_id": "2390",
            "source_customer_id": "60010",
            "source_timezone": "Europe/Amsterdam",
            "source_thread_id": "eurotikken:25:2390:60010",
            "messages": [
                {
                    "source_message_id": "5191811",
                    "source_sender_id": "2390",
                    "source_recipient_id": "60010",
                    "occurred_at": "2026-07-23T14:05:00",
                    "body": "Synthetic outbound message.",
                },
                {
                    "source_message_id": "5191813",
                    "source_sender_id": "60010",
                    "source_recipient_id": "2390",
                    "occurred_at": "2026-07-23T14:11:26.269135",
                    "body": "Synthetic inbound message.",
                },
            ],
        }

    def _write_payload(self, directory, payload=None):
        path = Path(directory) / "eurotikken-thread.json"
        selected = self._payload() if payload is None else payload
        path.write_text(json.dumps(selected), encoding="utf-8")
        return path

    def _call(self, path, **overrides):
        options = {
            "input": str(path),
            "creator_id": self.creator.id,
            "channel_id": self.channel.id,
            "site_id": "25",
            "profile_id": "2390",
            "customer_id": "60010",
            "limit": 50,
        }
        options.update(overrides)
        stdout = StringIO()
        call_command("import_eurotikken_thread", stdout=stdout, **options)
        return stdout.getvalue()

    def test_default_run_is_dry_run(self):
        with TemporaryDirectory() as directory:
            output = self._call(self._write_payload(directory))

        self.assertIn("DRY RUN", output)
        self.assertIn("would_create_messages=2", output)
        self.assertEqual(ConversationThread.objects.count(), 0)
        self.assertEqual(ConversationMessage.objects.count(), 0)

    def test_apply_creates_bounded_thread_and_messages(self):
        with TemporaryDirectory() as directory:
            output = self._call(self._write_payload(directory), apply=True)

        thread = ConversationThread.objects.get()
        messages = list(ConversationMessage.objects.order_by("occurred_at", "id"))

        self.assertIn("thread_created=True", output)
        self.assertIn("messages_created=2", output)
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
        self.assertEqual(
            thread.status,
            ConversationThread.Status.WAITING_ON_OPERATOR,
        )
        self.assertEqual(
            [message.direction for message in messages],
            [
                ConversationMessage.Direction.OUTBOUND,
                ConversationMessage.Direction.INBOUND,
            ],
        )
        self.assertEqual(
            [message.source_message_id for message in messages],
            [
                "eurotikken:messages:5191811",
                "eurotikken:messages:5191813",
            ],
        )
        self.assertEqual(messages[0].sender_label, "Sonja")
        self.assertEqual(messages[1].sender_label, "Eurotikken customer 60010")

        local_time = timezone.localtime(
            messages[1].occurred_at,
            ZoneInfo("Europe/Amsterdam"),
        )
        self.assertEqual(
            local_time.replace(tzinfo=None).isoformat(),
            "2026-07-23T14:11:26.269135",
        )

    def test_second_apply_is_idempotent(self):
        with TemporaryDirectory() as directory:
            path = self._write_payload(directory)
            self._call(path, apply=True)
            output = self._call(path, apply=True)

        self.assertIn("thread_created=False", output)
        self.assertIn("messages_created=0", output)
        self.assertIn("messages_skipped=2", output)
        self.assertEqual(ConversationThread.objects.count(), 1)
        self.assertEqual(ConversationMessage.objects.count(), 2)

    def test_rejects_payload_identity_mismatch(self):
        payload = self._payload()
        payload["source_site_id"] = "26"

        with TemporaryDirectory() as directory:
            path = self._write_payload(directory, payload)
            with self.assertRaisesMessage(CommandError, "source_site_id mismatch"):
                self._call(path)

    def test_rejects_limit_over_hard_maximum(self):
        with TemporaryDirectory() as directory:
            path = self._write_payload(directory)
            with self.assertRaisesMessage(
                CommandError,
                "--limit must be between 1 and 50",
            ):
                self._call(path, limit=51)

    def test_rejects_duplicate_message_ids(self):
        payload = self._payload()
        payload["messages"].append(dict(payload["messages"][0]))

        with TemporaryDirectory() as directory:
            path = self._write_payload(directory, payload)
            with self.assertRaisesMessage(
                CommandError,
                "Duplicate source_message_id",
            ):
                self._call(path)
