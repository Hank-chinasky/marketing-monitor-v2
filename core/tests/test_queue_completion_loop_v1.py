from datetime import timedelta
from urllib.parse import parse_qs, urlparse

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


class QueueCompletionLoopV1Tests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        user_model = get_user_model()

        self.user = user_model.objects.create_user(
            username="completion-operator",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.user)

        self.creator = Creator.objects.create(
            display_name="Completion Creator",
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
        )

        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="completion-account",
            profile_url="",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
        )

        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=self.now - timedelta(days=1),
            active=True,
        )

    def make_thread(
        self,
        source_thread_id,
        *,
        status=ConversationThread.Status.WAITING_ON_OPERATOR,
        minutes_ago=10,
        source_system=ConversationThread.SourceSystem.CHATTIES,
    ):
        return ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=source_system,
            source_thread_id=source_thread_id,
            source_site_id="completion-source",
            source_site_label="Completion source",
            status=status,
            last_message_at=self.now - timedelta(minutes=minutes_ago),
            thread_summary="Volledige completion-context.",
            open_loop="Pak de lopende lijn gecontroleerd op.",
            guardrails="Geen ongeverifieerde toezeggingen.",
            risk_flags="",
            last_handoff_note="Context is gecontroleerd.",
            last_approved_reply_style="Warm en persoonlijk.",
        )

    @staticmethod
    def query_values(response):
        return parse_qs(urlparse(response["Location"]).query)

    def test_warm_follow_up_completion_opens_next_thread(self):
        current = self.make_thread("COMPLETE-WARM", minutes_ago=5)
        next_thread = self.make_thread("COMPLETE-NEXT", minutes_ago=40)

        ThreadFollowUpStatus.objects.create(
            thread=current,
            status=ThreadFollowUpStatus.Status.WARM,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "thread": current.pk,
                "follow_up_status": ThreadFollowUpStatus.Status.WARM,
                "follow_up_note": "In de bron afgehandeld.",
                "queue_action": "save_and_next",
            },
        )

        self.assertEqual(response.status_code, 302)
        query = self.query_values(response)

        self.assertEqual(query["thread"], [str(next_thread.pk)])
        self.assertEqual(query["queue_saved"], ["follow_up"])
        self.assertEqual(query["queue_advanced"], ["1"])

        current.refresh_from_db()
        self.assertEqual(
            current.status,
            ConversationThread.Status.WAITING_ON_CUSTOMER,
        )

    def test_later_trigger_completion_parks_current_and_opens_next(self):
        current = self.make_thread("COMPLETE-LATER", minutes_ago=5)
        next_thread = self.make_thread("COMPLETE-LATER-NEXT", minutes_ago=35)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "thread": current.pk,
                "follow_up_status": (
                    ThreadFollowUpStatus.Status.LATER_TRIGGEREN
                ),
                "follow_up_note": "Later opnieuw bekijken.",
                "queue_action": "save_and_next",
            },
        )

        self.assertEqual(response.status_code, 302)
        query = self.query_values(response)
        self.assertEqual(query["thread"], [str(next_thread.pk)])

        follow_up = ThreadFollowUpStatus.objects.get(thread=current)
        self.assertEqual(
            follow_up.status,
            ThreadFollowUpStatus.Status.LATER_TRIGGEREN,
        )

    def test_review_completion_marks_handoff_and_opens_next(self):
        current = self.make_thread("COMPLETE-REVIEW", minutes_ago=5)
        next_thread = self.make_thread("COMPLETE-REVIEW-NEXT", minutes_ago=30)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "thread": current.pk,
                "follow_up_status": (
                    ThreadFollowUpStatus.Status.REVIEW_NODIG
                ),
                "follow_up_note": "Broncontrole vereist.",
                "queue_action": "save_and_next",
            },
        )

        self.assertEqual(response.status_code, 302)
        query = self.query_values(response)
        self.assertEqual(query["thread"], [str(next_thread.pk)])

        current.refresh_from_db()
        self.assertEqual(
            current.status,
            ConversationThread.Status.HANDOFF_REQUIRED,
        )

    def test_handoff_completion_opens_next_and_waits_on_customer(self):
        current = self.make_thread(
            "COMPLETE-HANDOFF",
            status=ConversationThread.Status.HANDOFF_REQUIRED,
            minutes_ago=5,
        )
        next_thread = self.make_thread(
            "COMPLETE-HANDOFF-NEXT",
            minutes_ago=25,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "thread": current.pk,
                "handoff_summary": "Actie in bron uitgevoerd.",
                "next_step": "Wacht op antwoord van de klant.",
                "blocker": "",
                "close_signal": "overdracht_klaar",
                "queue_action": "save_and_next",
            },
        )

        self.assertEqual(response.status_code, 302)
        query = self.query_values(response)

        self.assertEqual(query["thread"], [str(next_thread.pk)])
        self.assertEqual(query["queue_saved"], ["handoff"])
        self.assertEqual(query["queue_advanced"], ["1"])

        current.refresh_from_db()
        self.assertEqual(
            current.status,
            ConversationThread.Status.WAITING_ON_CUSTOMER,
        )
        self.assertIn(
            "Actie in bron uitgevoerd.",
            current.last_handoff_note,
        )

    def test_completion_without_other_active_thread_shows_end_state(self):
        current = self.make_thread("COMPLETE-LAST", minutes_ago=5)

        ThreadFollowUpStatus.objects.create(
            thread=current,
            status=ThreadFollowUpStatus.Status.WARM,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "thread": current.pk,
                "follow_up_status": ThreadFollowUpStatus.Status.WARM,
                "follow_up_note": "Laatste actieve gesprek afgehandeld.",
                "queue_action": "save_and_next",
            },
        )

        self.assertEqual(response.status_code, 302)
        query = self.query_values(response)

        self.assertEqual(query["thread"], [str(current.pk)])
        self.assertEqual(query["queue_cycle_complete"], ["1"])

        saved_response = self.client.get(response["Location"])
        self.assertContains(
            saved_response,
            "There is no other active conversation to open now.",
        )


    def test_save_and_next_stays_within_source_filter_and_preserves_focus(self):
        current = self.make_thread(
            "FILTER-CURRENT",
            minutes_ago=5,
        )
        cross_source = self.make_thread(
            "FILTER-EUROTIKKEN",
            minutes_ago=90,
            source_system=(
                ConversationThread.SourceSystem.EUROTIKKEN
            ),
        )
        next_chatties = self.make_thread(
            "FILTER-NEXT-CHATTIES",
            minutes_ago=30,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "thread": current.pk,
                "source": "chatties",
                "focus": "1",
                "follow_up_status": (
                    ThreadFollowUpStatus.Status.WARM
                ),
                "follow_up_note": (
                    "Binnen Chatties afgehandeld."
                ),
                "queue_action": "save_and_next",
            },
        )

        self.assertEqual(response.status_code, 302)
        query = self.query_values(response)

        self.assertEqual(
            query["thread"],
            [str(next_chatties.pk)],
        )
        self.assertNotEqual(
            query["thread"],
            [str(cross_source.pk)],
        )
        self.assertEqual(query["source"], ["chatties"])
        self.assertEqual(query["focus"], ["1"])
        self.assertEqual(
            query["queue_saved"],
            ["follow_up"],
        )
        self.assertEqual(
            query["queue_advanced"],
            ["1"],
        )

    def test_save_and_next_crosses_legacy_and_native_eurotikken_alias(self):
        current = self.make_thread(
            "FILTER-LEGACY-EUROTIKKEN",
            minutes_ago=5,
            source_system=(
                ConversationThread.SourceSystem.MARA_CHAT
            ),
        )
        next_eurotikken = self.make_thread(
            "FILTER-NATIVE-EUROTIKKEN",
            minutes_ago=30,
            source_system=(
                ConversationThread.SourceSystem.EUROTIKKEN
            ),
        )
        cross_source = self.make_thread(
            "FILTER-CHATTIES-OUTSIDE",
            minutes_ago=90,
            source_system=(
                ConversationThread.SourceSystem.CHATTIES
            ),
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "thread": current.pk,
                "source": "eurotikken",
                "focus": "1",
                "follow_up_status": (
                    ThreadFollowUpStatus.Status.WARM
                ),
                "follow_up_note": (
                    "Legacy Eurotikken-thread afgehandeld."
                ),
                "queue_action": "save_and_next",
            },
        )

        self.assertEqual(response.status_code, 302)
        query = self.query_values(response)

        self.assertEqual(
            query["thread"],
            [str(next_eurotikken.pk)],
        )
        self.assertNotEqual(
            query["thread"],
            [str(cross_source.pk)],
        )
        self.assertEqual(
            query["source"],
            ["eurotikken"],
        )
        self.assertEqual(query["focus"], ["1"])
        self.assertEqual(
            query["queue_saved"],
            ["follow_up"],
        )
        self.assertEqual(
            query["queue_advanced"],
            ["1"],
        )

    def test_workfloor_shows_direct_operator_action_with_focus_entry(self):
        current = self.make_thread(
            "FOCUSED-OPERATOR-SURFACE",
            minutes_ago=15,
        )

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("chat-hub"),
            {"thread": current.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operator workspace")
        self.assertContains(response, "Work queue")
        self.assertContains(response, "Messages")
        self.assertContains(response, "Buddy")
        self.assertContains(response, "Operator action")
        self.assertContains(response, "Trigger later")
        self.assertContains(response, "Cooled off")
        self.assertContains(response, "Review required")
        self.assertContains(response, "Save follow-up status")
        self.assertContains(response, "Save and open next")
        self.assertContains(
            response,
            "View conversations that need attention",
        )
        self.assertContains(response, "Open focus mode")
        self.assertNotContains(response, "Focus mode active")
        self.assertNotContains(response, "Focusstand verlaten")
