from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import BuddyDraft, ConversationThread, Creator, CreatorChannel, Operator, OperatorAssignment


class ConversationThreadViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin-thread-views",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_user = User.objects.create_user(
            username="operator-thread-views",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)
        self.no_assignment_user = User.objects.create_user(
            username="operator-no-assignment-thread-views",
            password="x",
            is_active=True,
        )
        self.no_assignment_operator = Operator.objects.create(user=self.no_assignment_user)

        self.creator_in_scope = Creator.objects.create(
            display_name="In Scope Creator",
            legal_name="In Scope Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.creator_out_of_scope = Creator.objects.create(
            display_name="Out Scope Creator",
            legal_name="Out Scope Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.creator_expired = Creator.objects.create(
            display_name="Expired Creator",
            legal_name="Expired Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.creator_inactive = Creator.objects.create(
            display_name="Inactive Creator",
            legal_name="Inactive Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )

        self.channel = CreatorChannel.objects.create(
            creator=self.creator_in_scope,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="inscope_creator",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
        )

        now = timezone.now()
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator_in_scope,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=now - timedelta(days=1),
            ends_at=None,
            active=True,
        )
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator_expired,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(hours=1),
            active=True,
        )
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator_inactive,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=now - timedelta(days=1),
            ends_at=None,
            active=False,
        )

        self.thread_in_scope = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            channel=self.channel,
            source_thread_id="mara-in-scope",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            thread_summary="Customer asked for a timing update.",
            open_loop="Confirm the next delivery slot.",
            guardrails="Do not promise a fixed hour.",
            risk_flags="Expectation risk.",
            last_handoff_note="Check latest schedule before replying.",
            last_approved_reply_style="Warm and clear.",
            last_message_at=now,
            last_operator_handoff_at=now - timedelta(minutes=30),
        )
        self.thread_out_of_scope = ConversationThread.objects.create(
            creator=self.creator_out_of_scope,
            source_thread_id="mara-out-scope",
        )
        self.thread_expired = ConversationThread.objects.create(
            creator=self.creator_expired,
            source_thread_id="mara-expired",
        )
        self.thread_inactive = ConversationThread.objects.create(
            creator=self.creator_inactive,
            source_thread_id="mara-inactive",
        )
        self.thread_without_channel = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            source_thread_id="mara-no-channel",
            thread_summary="No channel thread.",
        )

    def test_admin_sees_thread_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("conversation-thread-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mara-in-scope")
        self.assertContains(response, "mara-out-scope")
        self.assertContains(response, "mara-expired")
        self.assertContains(response, "mara-inactive")

    def test_scoped_operator_sees_only_threads_within_active_creator_assignment(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("conversation-thread-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mara-in-scope")
        self.assertContains(response, "mara-no-channel")
        self.assertNotContains(response, "mara-out-scope")
        self.assertNotContains(response, "mara-expired")
        self.assertNotContains(response, "mara-inactive")

    def test_operator_without_active_assignment_gets_200_with_empty_list(self):
        self.client.force_login(self.no_assignment_user)
        response = self.client.get(reverse("conversation-thread-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Geen conversation threads.")
        self.assertNotContains(response, "mara-in-scope")

    def test_operator_sees_detail_within_scope(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_in_scope.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.creator_in_scope.display_name)
        self.assertContains(response, "Customer asked for a timing update.")
        self.assertContains(response, "Confirm the next delivery slot.")
        self.assertContains(response, "Do not promise a fixed hour.")
        self.assertContains(response, "Expectation risk.")
        self.assertContains(response, "Check latest schedule before replying.")
        self.assertContains(response, "Warm and clear.")

    def test_operator_gets_404_on_detail_outside_scope(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_out_of_scope.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_expired_assignment_gives_no_detail_access(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_expired.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_inactive_assignment_gives_no_detail_access(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_inactive.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_detail_shows_latest_buddy_draft_if_present(self):
        old_draft = BuddyDraft.objects.create(
            thread=self.thread_in_scope,
            reply_text="Old draft reply",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.400"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )
        latest_draft = BuddyDraft.objects.create(
            thread=self.thread_in_scope,
            reply_text="Latest draft reply",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.500"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            requires_human_attention=True,
            handoff_note="Use manual review before sending.",
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_in_scope.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, latest_draft.reply_text)
        self.assertContains(response, "Use manual review before sending.")
        self.assertContains(response, "0.500")
        self.assertNotContains(response, old_draft.reply_text)

    def test_detail_works_without_channel(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_without_channel.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Geen channel gekoppeld.")

    def test_detail_works_without_draft(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_without_channel.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Geen BuddyDraft beschikbaar.")
