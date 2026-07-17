from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from core.management.commands.seed_buddy_demo_scenarios import (
    DEMO_CREATOR_NAME,
    DEMO_MARKER,
)
from core.models import (
    ConversationMessage,
    ConversationThread,
    Creator,
    Operator,
    OperatorAssignment,
    ThreadFollowUpStatus,
)


class SeedBuddyDemoScenariosTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo-operator",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.user)

    def seed(self):
        output = StringIO()
        call_command(
            "seed_buddy_demo_scenarios",
            username=self.user.username,
            stdout=output,
        )
        return output.getvalue()

    def test_command_creates_three_scoped_demo_scenarios(self):
        output = self.seed()

        creator = Creator.objects.get(
            display_name=DEMO_CREATOR_NAME,
            notes=DEMO_MARKER,
        )
        threads = ConversationThread.objects.filter(
            creator=creator,
        ).order_by("-last_message_at", "-id")

        self.assertEqual(threads.count(), 3)
        self.assertEqual(
            list(threads.values_list("source_thread_id", flat=True)),
            [
                "DEMO-01-WARME-FOLLOW-UP",
                "DEMO-02-REVIEW-NODIG",
                "DEMO-03-CONTEXT-ONTBREEKT",
            ],
        )
        self.assertTrue(
            OperatorAssignment.objects.filter(
                operator=self.operator,
                creator=creator,
                active=True,
            ).exists()
        )

        warm = threads.get(source_thread_id="DEMO-01-WARME-FOLLOW-UP")
        review = threads.get(source_thread_id="DEMO-02-REVIEW-NODIG")
        incomplete = threads.get(
            source_thread_id="DEMO-03-CONTEXT-ONTBREEKT"
        )

        self.assertEqual(
            warm.follow_up_status.status,
            ThreadFollowUpStatus.Status.WARM,
        )
        self.assertEqual(
            review.follow_up_status.status,
            ThreadFollowUpStatus.Status.REVIEW_NODIG,
        )
        self.assertTrue(review.risk_flags)
        self.assertIsNone(incomplete.channel)
        self.assertEqual(incomplete.thread_summary, "")
        self.assertEqual(incomplete.open_loop, "")
        self.assertFalse(
            ThreadFollowUpStatus.objects.filter(thread=incomplete).exists()
        )

        self.assertEqual(
            ConversationMessage.objects.filter(
                thread__creator=creator,
            ).count(),
            8,
        )
        self.assertIn("3 threads", output)

    def test_command_is_repeatable_without_duplicate_demo_data(self):
        self.seed()
        self.seed()

        self.assertEqual(
            Creator.objects.filter(
                display_name=DEMO_CREATOR_NAME,
                notes=DEMO_MARKER,
            ).count(),
            1,
        )
        self.assertEqual(
            ConversationThread.objects.filter(
                creator__notes=DEMO_MARKER,
            ).count(),
            3,
        )
        self.assertEqual(
            ConversationMessage.objects.filter(
                thread__creator__notes=DEMO_MARKER,
            ).count(),
            8,
        )

    def test_reset_removes_only_matching_demo_creator(self):
        normal_creator = Creator.objects.create(
            display_name="Normale Creator",
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.LEAD,
            notes="geen demo",
        )
        self.seed()

        output = StringIO()
        call_command(
            "seed_buddy_demo_scenarios",
            reset=True,
            stdout=output,
        )

        self.assertFalse(
            Creator.objects.filter(notes=DEMO_MARKER).exists()
        )
        self.assertTrue(
            Creator.objects.filter(pk=normal_creator.pk).exists()
        )
        self.assertIn("removed", output.getvalue().lower())
