from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import BuddyDraft, ConversationThread, Creator, CreatorChannel, Operator, OperatorAssignment


class BuddyDraftApproveActionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin-buddy-approve",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_user = User.objects.create_user(
            username="operator-buddy-approve",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)

        self.creator_in_scope = Creator.objects.create(
            display_name="Approve In Scope Creator",
            legal_name="Approve In Scope Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.creator_out_of_scope = Creator.objects.create(
            display_name="Approve Out Scope Creator",
            legal_name="Approve Out Scope Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator_in_scope,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="approve_scope_creator",
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

        self.operator_thread = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            channel=self.channel,
            source_thread_id="approve-operator-thread",
            thread_summary="Operator can approve this draft.",
        )
        self.operator_draft = BuddyDraft.objects.create(
            thread=self.operator_thread,
            reply_text="Operator draft reply",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.500"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

        self.admin_thread = ConversationThread.objects.create(
            creator=self.creator_out_of_scope,
            source_thread_id="approve-admin-thread",
            thread_summary="Admin can approve this out-of-scope draft.",
        )
        self.admin_draft = BuddyDraft.objects.create(
            thread=self.admin_thread,
            reply_text="Admin draft reply",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.500"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

        self.approved_thread = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            source_thread_id="approve-approved-thread",
        )
        self.approved_draft = BuddyDraft.objects.create(
            thread=self.approved_thread,
            reply_text="Already approved reply",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.500"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            state=BuddyDraft.State.APPROVED,
            generation_source=BuddyDraft.GenerationSource.STUB,
            approved_at=now - timedelta(minutes=5),
            approved_by_user=self.admin,
        )

        self.rejected_thread = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            source_thread_id="approve-rejected-thread",
        )
        self.rejected_draft = BuddyDraft.objects.create(
            thread=self.rejected_thread,
            reply_text="Rejected reply",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.500"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            state=BuddyDraft.State.REJECTED,
            generation_source=BuddyDraft.GenerationSource.STUB,
            rejected_at=now - timedelta(minutes=10),
        )

        self.no_draft_thread = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            source_thread_id="approve-no-draft-thread",
        )

        self.other_thread = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            source_thread_id="approve-other-thread",
            thread_summary="Other draft should stay untouched.",
        )
        self.other_draft = BuddyDraft.objects.create(
            thread=self.other_thread,
            reply_text="Other draft reply",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.500"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

        self.latest_policy_thread = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            source_thread_id="approve-latest-policy-thread",
        )
        self.older_draft = BuddyDraft.objects.create(
            thread=self.latest_policy_thread,
            reply_text="Older visible draft",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.400"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )
        self.latest_draft = BuddyDraft.objects.create(
            thread=self.latest_policy_thread,
            reply_text="Latest visible draft",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.500"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

    def approve_url(self, draft):
        return reverse("buddy-draft-approve", kwargs={"pk": draft.pk})

    def test_admin_can_approve_drafted_buddy_draft(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.approve_url(self.admin_draft))

        self.assertRedirects(
            response,
            reverse("conversation-thread-detail", kwargs={"pk": self.admin_thread.pk}),
        )

        self.admin_draft.refresh_from_db()
        self.assertEqual(self.admin_draft.state, BuddyDraft.State.APPROVED)
        self.assertIsNotNone(self.admin_draft.approved_at)
        self.assertEqual(self.admin_draft.approved_by_user, self.admin)
        self.assertIsNone(self.admin_draft.rejected_at)

    def test_scoped_operator_can_approve_drafted_buddy_draft(self):
        self.client.force_login(self.operator_user)
        response = self.client.post(self.approve_url(self.operator_draft))

        self.assertRedirects(
            response,
            reverse("conversation-thread-detail", kwargs={"pk": self.operator_thread.pk}),
        )

        self.operator_draft.refresh_from_db()
        self.assertEqual(self.operator_draft.state, BuddyDraft.State.APPROVED)
        self.assertIsNotNone(self.operator_draft.approved_at)
        self.assertEqual(self.operator_draft.approved_by_user, self.operator_user)
        self.assertIsNone(self.operator_draft.rejected_at)

    def test_out_of_scope_operator_gets_404(self):
        self.client.force_login(self.operator_user)
        response = self.client.post(self.approve_url(self.admin_draft))

        self.assertEqual(response.status_code, 404)
        self.admin_draft.refresh_from_db()
        self.assertEqual(self.admin_draft.state, BuddyDraft.State.DRAFTED)
        self.assertIsNone(self.admin_draft.approved_at)
        self.assertIsNone(self.admin_draft.approved_by_user)

    def test_approval_does_not_mutate_thread_or_other_drafts(self):
        original_thread_values = (
            self.operator_thread.status,
            self.operator_thread.thread_summary,
            self.operator_thread.last_handoff_note,
            self.operator_thread.updated_at,
        )
        other_draft_values = (
            self.other_draft.state,
            self.other_draft.approved_at,
            self.other_draft.approved_by_user_id,
        )

        self.client.force_login(self.operator_user)
        response = self.client.post(self.approve_url(self.operator_draft))
        self.assertEqual(response.status_code, 302)

        self.operator_thread.refresh_from_db()
        self.other_draft.refresh_from_db()

        self.assertEqual(
            original_thread_values,
            (
                self.operator_thread.status,
                self.operator_thread.thread_summary,
                self.operator_thread.last_handoff_note,
                self.operator_thread.updated_at,
            ),
        )
        self.assertEqual(
            other_draft_values,
            (
                self.other_draft.state,
                self.other_draft.approved_at,
                self.other_draft.approved_by_user_id,
            ),
        )

    def test_get_on_approve_route_returns_405(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.approve_url(self.admin_draft))

        self.assertEqual(response.status_code, 405)

    def test_detail_shows_approve_button_only_for_drafted_latest_draft(self):
        self.client.force_login(self.operator_user)

        drafted_response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.operator_thread.pk})
        )
        self.assertContains(drafted_response, "Markeer draft als goedgekeurd")
        self.assertContains(drafted_response, self.approve_url(self.operator_draft))

        latest_policy_response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.latest_policy_thread.pk})
        )
        self.assertContains(latest_policy_response, self.approve_url(self.latest_draft))
        self.assertNotContains(latest_policy_response, self.approve_url(self.older_draft))

        approved_response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.approved_thread.pk})
        )
        self.assertNotContains(approved_response, "Markeer draft als goedgekeurd")
        self.assertNotContains(approved_response, self.approve_url(self.approved_draft))

        rejected_response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.rejected_thread.pk})
        )
        self.assertNotContains(rejected_response, "Markeer draft als goedgekeurd")
        self.assertNotContains(rejected_response, self.approve_url(self.rejected_draft))

        no_draft_response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.no_draft_thread.pk})
        )
        self.assertNotContains(no_draft_response, "Markeer draft als goedgekeurd")

    def test_non_drafted_draft_cannot_be_reapproved(self):
        original_approved_at = self.approved_draft.approved_at
        original_approved_by_user = self.approved_draft.approved_by_user

        self.client.force_login(self.admin)
        response = self.client.post(self.approve_url(self.approved_draft))

        self.assertEqual(response.status_code, 404)
        self.approved_draft.refresh_from_db()
        self.assertEqual(self.approved_draft.state, BuddyDraft.State.APPROVED)
        self.assertEqual(self.approved_draft.approved_at, original_approved_at)
        self.assertEqual(self.approved_draft.approved_by_user, original_approved_by_user)
        self.assertIsNone(self.approved_draft.rejected_at)

    def test_second_approval_attempt_returns_404_and_leaves_object_untouched(self):
        self.client.force_login(self.admin)
        first_response = self.client.post(self.approve_url(self.admin_draft))
        self.assertEqual(first_response.status_code, 302)

        self.admin_draft.refresh_from_db()
        original_approved_at = self.admin_draft.approved_at
        original_approved_by_user = self.admin_draft.approved_by_user

        second_response = self.client.post(self.approve_url(self.admin_draft))
        self.assertEqual(second_response.status_code, 404)

        self.admin_draft.refresh_from_db()
        self.assertEqual(self.admin_draft.state, BuddyDraft.State.APPROVED)
        self.assertEqual(self.admin_draft.approved_at, original_approved_at)
        self.assertEqual(self.admin_draft.approved_by_user, original_approved_by_user)
        self.assertIsNone(self.admin_draft.rejected_at)

    def test_older_draft_cannot_be_approved_when_newer_latest_draft_exists(self):
        self.client.force_login(self.operator_user)
        response = self.client.post(self.approve_url(self.older_draft))

        self.assertEqual(response.status_code, 404)
        self.older_draft.refresh_from_db()
        self.latest_draft.refresh_from_db()
        self.assertEqual(self.older_draft.state, BuddyDraft.State.DRAFTED)
        self.assertIsNone(self.older_draft.approved_at)
        self.assertIsNone(self.older_draft.approved_by_user)
        self.assertEqual(self.latest_draft.state, BuddyDraft.State.DRAFTED)
        self.assertIsNone(self.latest_draft.approved_at)
        self.assertIsNone(self.latest_draft.approved_by_user)
