from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import BuddyDraft, ConversationThread, Creator, CreatorChannel, Operator, OperatorAssignment


class BuddyDraftDetailUITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin-buddy-draft-ui",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_user = User.objects.create_user(
            username="operator-buddy-draft-ui",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)

        self.creator_in_scope = Creator.objects.create(
            display_name="Draft UI Creator",
            legal_name="Draft UI Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.creator_out_of_scope = Creator.objects.create(
            display_name="Draft UI Out Scope",
            legal_name="Draft UI Out Scope BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator_in_scope,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="draft_ui_creator",
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

        self.thread_with_draft = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            channel=self.channel,
            source_thread_id="mara-draft-ui-1",
            thread_summary="Need a reply draft.",
        )
        self.thread_without_draft = ConversationThread.objects.create(
            creator=self.creator_in_scope,
            source_thread_id="mara-draft-ui-2",
            thread_summary="No draft yet.",
        )
        self.out_of_scope_thread = ConversationThread.objects.create(
            creator=self.creator_out_of_scope,
            source_thread_id="mara-draft-ui-3",
        )

        self.draft = BuddyDraft.objects.create(
            thread=self.thread_with_draft,
            reply_text="Dank je, ik kom hier handmatig op terug.",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.500"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            requires_human_attention=True,
            handoff_note="Controleer eerst de meest recente context.",
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

    def test_detail_renders_read_only_buddy_draft_block_for_latest_draft(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_with_draft.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Latest BuddyDraft")
        self.assertContains(response, "Draft status")
        self.assertContains(response, "Draft metadata")
        self.assertContains(response, "Reply draft")
        self.assertContains(response, "Handoff note")

    def test_detail_renders_empty_state_when_no_draft_exists(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_without_draft.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Er is nog geen BuddyDraft beschikbaar.")
        self.assertContains(response, "Draft-generatie volgt in een later ticket.")

    def test_detail_renders_buddy_draft_fields(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_with_draft.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dank je, ik kom hier handmatig op terug.")
        self.assertContains(response, "follow_up")
        self.assertContains(response, "calm")
        self.assertContains(response, "medium")
        self.assertContains(response, "Controleer eerst de meest recente context.")

    def test_detail_renders_requires_human_attention_state_and_generation_source(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_with_draft.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Requires human attention:")
        self.assertContains(response, "Ja")
        self.assertContains(response, "State:")
        self.assertContains(response, "drafted")
        self.assertContains(response, "Generation source:")
        self.assertContains(response, "stub")

    def test_detail_renders_placeholder_text_for_remaining_actions(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_with_draft.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Volgende fase")
        self.assertContains(response, "Aanvullende draft-acties volgen in een volgende fase.")
        self.assertContains(response, "Reject- en verzendflow worden later toegevoegd.")
        self.assertNotContains(response, "Reject")
        self.assertNotContains(response, "Generate")
        self.assertNotContains(response, "Send")

    def test_detail_now_renders_real_approve_button_for_drafted_latest_draft(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_with_draft.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Markeer draft als goedgekeurd")
        self.assertContains(response, reverse("buddy-draft-approve", kwargs={"pk": self.draft.pk}))

    def test_existing_scope_access_remains_intact(self):
        self.client.force_login(self.admin)
        admin_response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_with_draft.pk})
        )
        self.assertEqual(admin_response.status_code, 200)

        self.client.force_login(self.operator_user)
        operator_response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.thread_with_draft.pk})
        )
        self.assertEqual(operator_response.status_code, 200)

    def test_out_of_scope_detail_remains_404(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(
            reverse("conversation-thread-detail", kwargs={"pk": self.out_of_scope_thread.pk})
        )

        self.assertEqual(response.status_code, 404)
