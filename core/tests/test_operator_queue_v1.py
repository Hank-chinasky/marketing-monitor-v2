from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import (
    ConversationThread,
    Creator,
    CreatorChannel,
    Operator,
    OperatorAssignment,
    ThreadFollowUpStatus,
)
from core.services.operator_queue import (
    GROUP_LATER,
    GROUP_NOW,
    GROUP_REVIEW,
    GROUP_WAITING,
    build_operator_queue,
)


class OperatorPressureQueueV1Tests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        user_model = get_user_model()

        self.user = user_model.objects.create_user(
            username="pressure-operator",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.user)

        self.creator = Creator.objects.create(
            display_name="Queue Creator",
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
        )

        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=self.now - timedelta(days=1),
            active=True,
        )

        self.channel_a = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="queue-account-a",
            profile_url="",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
        )
        self.channel_b = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="queue-account-b",
            profile_url="",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
        )

    def make_thread(
        self,
        *,
        source_system,
        source_thread_id,
        source_label,
        channel,
        status,
        minutes_ago,
        risk_flags="",
        open_loop="Pak de lopende context gecontroleerd op.",
        guardrails="Geen ongeverifieerde toezeggingen.",
        handoff="Lopende context is gecontroleerd.",
    ):
        return ConversationThread.objects.create(
            creator=self.creator,
            channel=channel,
            source_system=source_system,
            source_thread_id=source_thread_id,
            source_site_id=f"site-{source_thread_id}",
            source_site_label=source_label,
            status=status,
            last_message_at=self.now - timedelta(minutes=minutes_ago),
            thread_summary="Queue testcontext.",
            open_loop=open_loop,
            guardrails=guardrails,
            risk_flags=risk_flags,
            last_handoff_note=handoff,
            last_approved_reply_style="Warm en persoonlijk.",
        )

    def test_warm_waiting_thread_is_first_action(self):
        warm = self.make_thread(
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id="QUEUE-WARM",
            source_label="Legacychat A",
            channel=self.channel_a,
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            minutes_ago=5,
        )
        ThreadFollowUpStatus.objects.create(
            thread=warm,
            status=ThreadFollowUpStatus.Status.WARM,
        )

        regular = self.make_thread(
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="QUEUE-REGULAR",
            source_label="Chatsource B",
            channel=self.channel_b,
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            minutes_ago=45,
        )

        queue = build_operator_queue(
            [regular, warm],
            now=self.now,
        )

        self.assertEqual(queue["next_item"]["thread"], warm)
        self.assertEqual(
            queue["next_item"]["group"],
            GROUP_NOW,
        )
        self.assertEqual(
            queue["next_item"]["priority_label"],
            "P1",
        )

    def test_review_thread_is_active_but_separate(self):
        review = self.make_thread(
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="QUEUE-REVIEW",
            source_label="Chatsource B",
            channel=self.channel_b,
            status=ConversationThread.Status.HANDOFF_REQUIRED,
            minutes_ago=20,
            risk_flags="Broncontext spreekt de afspraak tegen.",
        )

        queue = build_operator_queue([review], now=self.now)
        item = queue["active_items"][0]

        self.assertEqual(item["group"], GROUP_REVIEW)
        self.assertIn("risk signal", item["why_now"])
        self.assertEqual(item["reliability"], "Low")

    def test_waiting_customer_and_later_trigger_are_parked(self):
        waiting = self.make_thread(
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id="QUEUE-WAITING",
            source_label="Legacychat A",
            channel=self.channel_a,
            status=ConversationThread.Status.WAITING_ON_CUSTOMER,
            minutes_ago=10,
        )
        later = self.make_thread(
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="QUEUE-LATER",
            source_label="Chatsource B",
            channel=self.channel_b,
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            minutes_ago=30,
        )
        ThreadFollowUpStatus.objects.create(
            thread=later,
            status=ThreadFollowUpStatus.Status.LATER_TRIGGEREN,
        )

        queue = build_operator_queue(
            [waiting, later],
            now=self.now,
        )

        groups = {
            item["thread"].pk: item["group"]
            for item in queue["parked_items"]
        }

        self.assertEqual(groups[waiting.pk], GROUP_WAITING)
        self.assertEqual(groups[later.pk], GROUP_LATER)
        self.assertIsNone(queue["next_item"])

    def test_queue_is_source_aware_and_exposes_next_action(self):
        thread = self.make_thread(
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id="QUEUE-SOURCE",
            source_label="Legacychat A",
            channel=self.channel_a,
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            minutes_ago=65,
            open_loop="Beantwoord de open vraag zonder contextreset.",
        )

        queue = build_operator_queue([thread], now=self.now)
        item = queue["items"][0]

        self.assertEqual(item["source_label"], "Legacychat A")
        self.assertEqual(item["source_account"], "queue-account-a")
        self.assertEqual(
            item["next_action"],
            "Beantwoord de open vraag zonder contextreset.",
        )
        self.assertEqual(queue["counts"]["sources"], 1)

    def test_queue_counts_legacy_and_native_eurotikken_as_one_source(self):
        legacy = self.make_thread(
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="QUEUE-LEGACY-EUROTIKKEN",
            source_label="",
            channel=self.channel_a,
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            minutes_ago=10,
        )
        native = self.make_thread(
            source_system=ConversationThread.SourceSystem.EUROTIKKEN,
            source_thread_id="QUEUE-NATIVE-EUROTIKKEN",
            source_label="",
            channel=self.channel_b,
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            minutes_ago=20,
        )

        queue = build_operator_queue(
            [legacy, native],
            now=self.now,
        )

        self.assertEqual(queue["counts"]["sources"], 1)
        self.assertEqual(
            {
                item["source_label"]
                for item in queue["items"]
            },
            {"Eurotikken"},
        )

    def test_chat_hub_renders_cross_source_queue_for_operator(self):
        warm = self.make_thread(
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id="QUEUE-UI-WARM",
            source_label="Legacychat A",
            channel=self.channel_a,
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            minutes_ago=5,
        )
        ThreadFollowUpStatus.objects.create(
            thread=warm,
            status=ThreadFollowUpStatus.Status.WARM,
        )

        self.make_thread(
            source_system=ConversationThread.SourceSystem.MARA_CHAT,
            source_thread_id="QUEUE-UI-REVIEW",
            source_label="Chatsource B",
            channel=self.channel_b,
            status=ConversationThread.Status.HANDOFF_REQUIRED,
            minutes_ago=20,
            risk_flags="Review nodig.",
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shared operator queue")
        self.assertContains(response, "Open next conversation")
        self.assertContains(response, "Legacychat A")
        self.assertContains(response, "Chatsource B")
        self.assertContains(response, "Warm revenue moment")
        self.assertEqual(
            response.context["operator_queue"]["next_item"]["thread"],
            warm,
        )
