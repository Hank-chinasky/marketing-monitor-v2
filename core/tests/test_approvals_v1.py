from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Approval, ConversationThread, Creator, CreatorChannel, Operator, OperatorAssignment


class ApprovalsV1Tests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="approvals-operator",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.user)

        self.other_user = user_model.objects.create_user(
            username="approvals-other-operator",
            password="x",
            is_active=True,
        )
        self.other_operator = Operator.objects.create(user=self.other_user)

        self.creator = Creator.objects.create(
            display_name="Approval Creator",
            legal_name="Approval Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            content_source_url="https://example.com/source",
            content_ready_status=Creator.ContentReadyStatus.READY_TO_POST,
        )
        self.other_creator = Creator.objects.create(
            display_name="Out Scope Creator",
            legal_name="Out Scope Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            content_source_url="https://example.com/source-2",
            content_ready_status=Creator.ContentReadyStatus.READY_TO_POST,
        )

        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="approval-channel",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
            session_next_action="Review final post text.",
            session_updated_at=timezone.now(),
        )

        self.thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_thread_id="approval-thread",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            open_loop="Need explicit approval before publish.",
            guardrails="No promises.",
            last_handoff_note="Check with lead first.",
        )

        self.other_thread = ConversationThread.objects.create(
            creator=self.other_creator,
            source_thread_id="out-scope-thread",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            open_loop="Other scope action.",
            guardrails="Out scope guardrail.",
            last_handoff_note="Out of scope handoff.",
        )

        now = timezone.now()
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=now - timedelta(days=1),
            active=True,
        )
        OperatorAssignment.objects.create(
            operator=self.other_operator,
            creator=self.other_creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=now - timedelta(days=1),
            active=True,
        )

    def test_approval_model_supports_required_types_and_statuses(self):
        approval = Approval.objects.create(
            creator=self.creator,
            thread=self.thread,
            approval_type=Approval.Type.CONTENT_APPROVAL,
            status=Approval.Status.PENDING,
            summary="Publish response needs manual check.",
            requested_by=self.user,
        )

        self.assertEqual(approval.approval_type, Approval.Type.CONTENT_APPROVAL)
        self.assertEqual(approval.status, Approval.Status.PENDING)
        self.assertIn(("action_approval", "Action approval"), Approval.Type.choices)
        self.assertIn(("access_exception", "Access exception"), Approval.Type.choices)
        self.assertIn(("expired", "Expired"), Approval.Status.choices)

    def test_chat_workspace_shows_approval_status(self):
        Approval.objects.create(
            creator=self.creator,
            thread=self.thread,
            approval_type=Approval.Type.ACTION_APPROVAL,
            status=Approval.Status.PENDING,
            summary="Need go/no-go for sensitive reply.",
            requested_by=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertContains(response, "Approvals v1")
        self.assertContains(response, "Pending")
        self.assertContains(response, "Action approval")

    def test_feeder_workspace_shows_approval_status(self):
        Approval.objects.create(
            creator=self.creator,
            approval_type=Approval.Type.ACCESS_EXCEPTION,
            status=Approval.Status.APPROVED,
            summary="Temporary access exception accepted.",
            requested_by=self.user,
            decided_by=self.user,
            decided_at=timezone.now(),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"), {"creator": self.creator.pk})

        self.assertContains(response, "Approvals v1")
        self.assertContains(response, "Approved")
        self.assertContains(response, "Access exception")

    def test_create_action_adds_approval_and_run_log_message_in_chat(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-create"),
            {
                "workspace": "chats",
                "thread": self.thread.pk,
                "approval_type": Approval.Type.CONTENT_APPROVAL,
                "summary": "Check legal sensitivity.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Approval.objects.filter(
                creator=self.creator,
                thread=self.thread,
                approval_type=Approval.Type.CONTENT_APPROVAL,
                status=Approval.Status.PENDING,
            ).exists()
        )
        self.assertContains(response, "Approval aangemaakt")
        self.assertContains(response, "Content approval")

    def test_create_action_adds_approval_and_run_log_message_in_feeder(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-create"),
            {
                "workspace": "feeder",
                "creator": self.creator.pk,
                "approval_type": Approval.Type.ACCESS_EXCEPTION,
                "summary": "Need temporary access exception.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Approval.objects.filter(
                creator=self.creator,
                thread__isnull=True,
                approval_type=Approval.Type.ACCESS_EXCEPTION,
                status=Approval.Status.PENDING,
            ).exists()
        )
        self.assertContains(response, "Approval aangemaakt")
        self.assertContains(response, "Access exception")

    def test_create_out_of_scope_thread_fails_closed(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-create"),
            {
                "workspace": "chats",
                "thread": self.other_thread.pk,
                "approval_type": Approval.Type.ACTION_APPROVAL,
                "summary": "Should not be created.",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Approval.objects.filter(
                creator=self.other_creator,
                thread=self.other_thread,
            ).exists()
        )

    def test_create_out_of_scope_creator_fails_closed(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-create"),
            {
                "workspace": "feeder",
                "creator": self.other_creator.pk,
                "approval_type": Approval.Type.ACCESS_EXCEPTION,
                "summary": "Should not be created.",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Approval.objects.filter(
                creator=self.other_creator,
                thread__isnull=True,
            ).exists()
        )

    def test_create_rejects_thread_creator_mismatch(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-create"),
            {
                "workspace": "chats",
                "thread": self.thread.pk,
                "creator": self.other_creator.pk,
                "approval_type": Approval.Type.CONTENT_APPROVAL,
                "summary": "Mismatched payload.",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Approval.objects.filter(
                summary="Mismatched payload.",
            ).exists()
        )

    def test_create_rejects_feeder_thread_injection(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-create"),
            {
                "workspace": "feeder",
                "creator": self.creator.pk,
                "thread": self.thread.pk,
                "approval_type": Approval.Type.CONTENT_APPROVAL,
                "summary": "Injected thread should fail.",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            Approval.objects.filter(
                creator=self.creator,
                summary="Injected thread should fail.",
            ).exists()
        )

    def test_approve_action_updates_status_and_run_log_event(self):
        approval = Approval.objects.create(
            creator=self.creator,
            thread=self.thread,
            approval_type=Approval.Type.CONTENT_APPROVAL,
            status=Approval.Status.PENDING,
            requested_by=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-approve", kwargs={"pk": approval.pk}),
            follow=True,
        )

        approval.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(approval.status, Approval.Status.APPROVED)
        self.assertEqual(approval.decided_by, self.user)
        self.assertIsNotNone(approval.decided_at)
        self.assertContains(response, "Approval goedgekeurd")

    def test_reject_action_updates_status_and_run_log_event(self):
        approval = Approval.objects.create(
            creator=self.creator,
            approval_type=Approval.Type.ACTION_APPROVAL,
            status=Approval.Status.PENDING,
            requested_by=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-reject", kwargs={"pk": approval.pk}),
            follow=True,
        )

        approval.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(approval.status, Approval.Status.REJECTED)
        self.assertEqual(approval.decided_by, self.user)
        self.assertIsNotNone(approval.decided_at)
        self.assertContains(response, "Approval afgewezen")

    def test_out_of_scope_approval_actions_fail_closed(self):
        approval = Approval.objects.create(
            creator=self.other_creator,
            approval_type=Approval.Type.ACCESS_EXCEPTION,
            status=Approval.Status.PENDING,
            requested_by=self.other_user,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("approval-approve", kwargs={"pk": approval.pk}),
        )

        self.assertEqual(response.status_code, 404)
        approval.refresh_from_db()
        self.assertEqual(approval.status, Approval.Status.PENDING)

    def test_approve_on_non_pending_returns_404_and_does_not_mutate(self):
        blocked_statuses = [
            Approval.Status.APPROVED,
            Approval.Status.REJECTED,
            Approval.Status.EXPIRED,
            Approval.Status.NOT_REQUIRED,
        ]

        self.client.force_login(self.user)
        for status in blocked_statuses:
            with self.subTest(status=status):
                approval = Approval.objects.create(
                    creator=self.creator,
                    thread=self.thread,
                    approval_type=Approval.Type.CONTENT_APPROVAL,
                    status=status,
                    requested_by=self.user,
                    decided_by=self.user if status != Approval.Status.NOT_REQUIRED else None,
                    decided_at=timezone.now()
                    if status != Approval.Status.NOT_REQUIRED
                    else None,
                )
                decided_at_before = approval.decided_at

                response = self.client.post(
                    reverse("approval-approve", kwargs={"pk": approval.pk}),
                )

                self.assertEqual(response.status_code, 404)
                approval.refresh_from_db()
                self.assertEqual(approval.status, status)
                self.assertEqual(approval.decided_at, decided_at_before)

    def test_reject_on_non_pending_returns_404_and_does_not_mutate(self):
        blocked_statuses = [
            Approval.Status.APPROVED,
            Approval.Status.REJECTED,
            Approval.Status.EXPIRED,
            Approval.Status.NOT_REQUIRED,
        ]

        self.client.force_login(self.user)
        for status in blocked_statuses:
            with self.subTest(status=status):
                approval = Approval.objects.create(
                    creator=self.creator,
                    approval_type=Approval.Type.ACTION_APPROVAL,
                    status=status,
                    requested_by=self.user,
                    decided_by=self.user if status != Approval.Status.NOT_REQUIRED else None,
                    decided_at=timezone.now()
                    if status != Approval.Status.NOT_REQUIRED
                    else None,
                )
                decided_at_before = approval.decided_at

                response = self.client.post(
                    reverse("approval-reject", kwargs={"pk": approval.pk}),
                )

                self.assertEqual(response.status_code, 404)
                approval.refresh_from_db()
                self.assertEqual(approval.status, status)
                self.assertEqual(approval.decided_at, decided_at_before)
