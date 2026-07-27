import json

from django.test import TestCase

from core.models import (
    ConversationContextSnapshot,
    ConversationThread,
    Creator,
)
from core.services.operator_context import (
    build_operator_context,
)


class OperatorContextTests(TestCase):
    def setUp(self):
        self.creator = Creator.objects.create(
            display_name="Sonja",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.thread = ConversationThread.objects.create(
            creator=self.creator,
            source_system=ConversationThread.SourceSystem.EUROTIKKEN,
            source_thread_id="eurotikken:25:2390:60010",
            source_site_id="25",
        )
        self.snapshot = (
            ConversationContextSnapshot.objects.create(
                thread=self.thread,
                schema_version=(
                    "eurotikken-operator-context-v1"
                ),
                source_sha256="a" * 64,
                profile_context={
                    "display_name": "Sonja",
                    "age": 53,
                    "city": "Geleen",
                    "region": "Limburg",
                    "country": "Nederland",
                    "marital_status": "Gescheiden",
                    "goal": "Liefde",
                    "occupation": (
                        "Administratief medewerkster"
                    ),
                    "summary": (
                        "Sinds kort weer vrijgezel"
                    ),
                    "source_checked": True,
                    "source_reviewed": True,
                },
                customer_context={
                    "display_name": "jupke",
                    "age": 77,
                    "city": "",
                    "region": "Limburg",
                    "country": "Nederland",
                    "marital_status": "Weduwnaar",
                    "goal": "Samen Genieten",
                    "source_checked": False,
                    "source_reviewed": True,
                },
                customer_media=[
                    {
                        "source_media_id": "50429",
                        "source_owner_user_id": "60055",
                        "source_path": (
                            "uploaded_files/"
                            "000000_jan.JPG"
                        ),
                        "media_type": "image",
                        "is_primary": True,
                        "active": True,
                        "allow_external_ai": False,
                        "requires_operator_reveal": True,
                        "default_visibility": "covered",
                    }
                ],
            )
        )

    def test_builds_compact_operator_context(self):
        context = build_operator_context(self.thread)

        self.assertTrue(context["available"])
        self.assertEqual(
            context["profile"]["display_name"],
            "Sonja",
        )
        self.assertEqual(
            context["profile"]["occupation"],
            "Administratief medewerkster",
        )
        self.assertEqual(
            context["customer"]["display_name"],
            "jupke",
        )
        self.assertTrue(
            context["customer_reliability_warning"]
        )

    def test_builds_media_url_only_from_hard_mapping(self):
        context = build_operator_context(self.thread)

        self.assertEqual(
            context["customer_media"],
            [
                {
                    "source_media_id": "50429",
                    "reveal_url": (
                        "https://datesamen.nl/media/"
                        "uploaded_files/000000_jan.JPG"
                    ),
                    "is_primary": True,
                }
            ],
        )

        serialized = json.dumps(context)

        self.assertNotIn("source_path", serialized)
        self.assertNotIn("source_owner_user_id", serialized)

    def test_unknown_source_mapping_returns_no_media_url(self):
        self.thread.source_site_id = "999"
        self.thread.save(update_fields=["source_site_id"])

        context = build_operator_context(self.thread)

        self.assertTrue(context["available"])
        self.assertEqual(context["customer_media"], [])

    def test_missing_snapshot_returns_unavailable_context(self):
        self.snapshot.delete()

        context = build_operator_context(self.thread)

        self.assertFalse(context["available"])
        self.assertEqual(context["customer_media"], [])
