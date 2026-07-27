import copy
import hashlib
import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from core.models import (
    ConversationContextSnapshot,
    ConversationThread,
    Creator,
    CreatorChannel,
)


class ImportEurotikkenOperatorContextTests(TestCase):
    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)

        self.creator = Creator.objects.create(
            display_name="Sonja",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="eurotikken-sonja",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
        )
        self.thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.EUROTIKKEN,
            source_thread_id="eurotikken:25:2390:60010",
            source_site_id="25",
            source_profile_label="Sonja",
            source_profile_username="Sonja",
            source_customer_label="jupke",
            source_customer_username="jupke",
        )

    def build_payload(self):
        return {
            "schema_version": "eurotikken-operator-context-v1",
            "source_system": "eurotikken",
            "source_site_id": "25",
            "source_site_label": "DateSamen",
            "source_profile_id": "2390",
            "source_customer_id": "60010",
            "source_customer_user_id": "60055",
            "source_thread_id": "eurotikken:25:2390:60010",
            "profile_context": {
                "display_name": "Sonja",
                "age": 53,
                "city": "Geleen",
                "region": "Limburg",
                "country": "Nederland",
                "marital_status": {
                    "value": "Gescheiden",
                    "source": "synthetic",
                },
                "goal": "Liefde",
                "occupation": "Administratief medewerkster",
                "profile_summary": "Sinds kort weer vrijgezel",
                "birth_date": "1973-01-01",
                "profile_extra_info": "niet bewaren",
                "source_checked": True,
                "source_reviewed": True,
                "source_profile_id": "2390",
                "source_user_id": "2390",
            },
            "customer_context": {
                "display_name": "jupke",
                "age": 77,
                "city": "",
                "region": "Limburg",
                "country": "Nederland",
                "marital_status": {
                    "value": "Weduwnaar",
                    "source": "synthetic",
                },
                "goal": "Samen Genieten",
                "occupation": "",
                "profile_summary": "",
                "birth_date": "1949-01-01",
                "profile_extra_info": "niet bewaren",
                "source_checked": False,
                "source_reviewed": True,
                "source_profile_id": "60010",
                "source_user_id": "60055",
            },
            "profile_media": [
                {
                    "source_media_id": "100",
                    "source_owner_user_id": "2390",
                    "source_path": "uploaded_files/sonja.webp",
                    "media_type": "image",
                    "is_primary": True,
                    "active": True,
                    "allow_external_ai": False,
                    "requires_operator_reveal": True,
                    "default_visibility": "covered",
                }
            ],
            "customer_media": [
                {
                    "source_media_id": "50429",
                    "source_owner_user_id": "60055",
                    "source_path": "uploaded_files/000000_jan.JPG",
                    "media_type": "image",
                    "is_primary": True,
                    "active": True,
                    "allow_external_ai": False,
                    "requires_operator_reveal": True,
                    "default_visibility": "covered",
                }
            ],
            "media_policy": {
                "binary_content_included": False,
                "load_only_after_operator_action": True,
                "allow_external_ai": False,
                "allow_automatic_image_analysis": False,
            },
            "data_quality": {
                "profile_reliability": "high",
                "customer_reliability": "medium",
                "warnings": [
                    {
                        "code": "customer_not_source_checked",
                        "field": "customer_context",
                        "canonical_value": "sensitive-value",
                        "resolution": "operator review",
                    }
                ],
            },
            "unknown_top_level": {
                "must": "not be stored",
            },
        }

    def write_payload(self, payload):
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
        path = (
            Path(self.temp_directory.name)
            / "synthetic-context.json"
        )
        path.write_bytes(encoded)
        return path, hashlib.sha256(encoded).hexdigest()

    def run_command(
        self,
        payload=None,
        *,
        apply=False,
        creator_id=None,
        channel_id=None,
        site_id="25",
        profile_id="2390",
        customer_id="60010",
        expected_sha256=None,
    ):
        payload = copy.deepcopy(
            payload if payload is not None
            else self.build_payload()
        )
        path, actual_sha256 = self.write_payload(payload)

        stdout = StringIO()

        call_command(
            "import_eurotikken_operator_context",
            input=str(path),
            expected_sha256=(
                expected_sha256
                if expected_sha256 is not None
                else actual_sha256
            ),
            creator_id=(
                self.creator.pk
                if creator_id is None
                else creator_id
            ),
            channel_id=(
                self.channel.pk
                if channel_id is None
                else channel_id
            ),
            site_id=site_id,
            profile_id=profile_id,
            customer_id=customer_id,
            apply=apply,
            stdout=stdout,
        )

        return stdout.getvalue()

    def test_dry_run_creates_no_snapshot(self):
        output = self.run_command()

        self.assertEqual(
            ConversationContextSnapshot.objects.count(),
            0,
        )
        self.assertIn(
            "DRY RUN — no database changes.",
            output,
        )
        self.assertIn(
            "would_create_context_snapshot=True",
            output,
        )

    def test_apply_creates_exactly_one_normalized_snapshot(self):
        output = self.run_command(apply=True)

        self.assertEqual(
            ConversationContextSnapshot.objects.count(),
            1,
        )

        snapshot = ConversationContextSnapshot.objects.get()
        self.assertEqual(snapshot.thread, self.thread)
        self.assertEqual(
            snapshot.profile_context["display_name"],
            "Sonja",
        )
        self.assertEqual(
            snapshot.customer_context["display_name"],
            "jupke",
        )
        self.assertNotIn(
            "birth_date",
            snapshot.profile_context,
        )
        self.assertNotIn(
            "profile_extra_info",
            snapshot.customer_context,
        )
        self.assertNotIn(
            "unknown_top_level",
            snapshot.data_quality,
        )
        self.assertNotIn(
            "canonical_value",
            snapshot.data_quality["warnings"][0],
        )
        self.assertIn("snapshot_created=True", output)

    def test_second_apply_is_idempotent(self):
        self.run_command(apply=True)
        snapshot_id = (
            ConversationContextSnapshot.objects.get().pk
        )

        output = self.run_command(apply=True)

        self.assertEqual(
            ConversationContextSnapshot.objects.count(),
            1,
        )
        self.assertEqual(
            ConversationContextSnapshot.objects.get().pk,
            snapshot_id,
        )
        self.assertIn("snapshot_created=False", output)
        self.assertIn("snapshot_updated=True", output)

    def test_wrong_checksum_is_rejected(self):
        with self.assertRaisesMessage(
            CommandError,
            "Input SHA-256 does not match.",
        ):
            self.run_command(
                expected_sha256="0" * 64,
            )

    def test_wrong_schema_version_is_rejected(self):
        payload = self.build_payload()
        payload["schema_version"] = "wrong-schema"

        with self.assertRaisesMessage(
            CommandError,
            "schema_version must be",
        ):
            self.run_command(payload)

    def test_wrong_source_arguments_are_rejected(self):
        cases = [
            {"site_id": "99"},
            {"profile_id": "9999"},
            {"customer_id": "99999"},
        ]

        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(CommandError):
                    self.run_command(**arguments)

    def test_wrong_payload_source_ids_are_rejected(self):
        cases = [
            ("source_profile_id", "9999"),
            ("source_customer_id", "99999"),
            (
                "source_thread_id",
                "eurotikken:25:9999:99999",
            ),
        ]

        for field, value in cases:
            payload = self.build_payload()
            payload[field] = value

            with self.subTest(field=field):
                with self.assertRaises(CommandError):
                    self.run_command(payload)

    def test_missing_thread_is_rejected(self):
        self.thread.delete()

        with self.assertRaisesMessage(
            CommandError,
            "Existing Eurotikken ConversationThread was not found.",
        ):
            self.run_command()

    def test_creator_and_channel_mismatch_are_rejected(self):
        with self.assertRaisesMessage(
            CommandError,
            "creator-id does not match",
        ):
            self.run_command(
                creator_id=self.creator.pk + 999,
            )

        with self.assertRaisesMessage(
            CommandError,
            "channel-id does not match",
        ):
            self.run_command(
                channel_id=self.channel.pk + 999,
            )

    def test_parent_traversal_media_path_is_rejected(self):
        payload = self.build_payload()
        payload["customer_media"][0][
            "source_path"
        ] = "uploaded_files/../secret.jpg"

        with self.assertRaisesMessage(
            CommandError,
            "unsafe path segment",
        ):
            self.run_command(payload)

    def test_full_https_media_url_is_rejected(self):
        payload = self.build_payload()
        payload["customer_media"][0][
            "source_path"
        ] = "https://example.com/image.jpg"

        with self.assertRaises(CommandError):
            self.run_command(payload)

    def test_external_ai_media_permission_is_rejected(self):
        payload = self.build_payload()
        payload["customer_media"][0][
            "allow_external_ai"
        ] = True

        with self.assertRaisesMessage(
            CommandError,
            "allow_external_ai must be false",
        ):
            self.run_command(payload)

    def test_binary_content_policy_is_rejected(self):
        payload = self.build_payload()
        payload["media_policy"][
            "binary_content_included"
        ] = True

        with self.assertRaisesMessage(
            CommandError,
            "binary_content_included must be false",
        ):
            self.run_command(payload)
