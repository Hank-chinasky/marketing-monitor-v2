from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import (
    Approval,
    BuddyDraft,
    ConversationThread,
    Creator,
    CreatorChannel,
    Operator,
    OperatorAssignment,
    ThreadFollowUpStatus,
)
from core.services.demo_access import (
    DEMO_DATA_MARKER,
    DEMO_VIEWER_GROUP_NAME,
)


class DemoReadOnlyAccessV1Tests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.demo_user = user_model.objects.create_user(
            username="demo-viewer",
            password="x",
            is_active=True,
        )
        demo_group = Group.objects.create(name=DEMO_VIEWER_GROUP_NAME)
        self.demo_user.groups.add(demo_group)

        self.demo_creator = Creator.objects.create(
            display_name="Luna",
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
            notes=DEMO_DATA_MARKER,
        )
        self.demo_channel = CreatorChannel.objects.create(
            creator=self.demo_creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="demo-readonly-luna",
            profile_url="https://example.com/demo/luna",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.DRAFT_ONLY,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
        )
        self.demo_thread = ConversationThread.objects.create(
            creator=self.demo_creator,
            channel=self.demo_channel,
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id="DEMO-READONLY-THREAD",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            last_message_at=timezone.now(),
            thread_summary="Fictieve warme democontext.",
            open_loop="Bekijk de volgende operatorstap.",
            guardrails="Geen automatische actie.",
            last_handoff_note="Demo-handoff is alleen ter inzage.",
            last_approved_reply_style="Warm en persoonlijk.",
        )

        self.live_creator = Creator.objects.create(
            display_name="Live Creator",
            legal_name="Live Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
            notes="live-data",
        )
        self.live_channel = CreatorChannel.objects.create(
            creator=self.live_creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="live-readonly-test",
            profile_url="https://example.com/live",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
        )
        self.live_thread = ConversationThread.objects.create(
            creator=self.live_creator,
            channel=self.live_channel,
            source_thread_id="LIVE-THREAD-MUST-NOT-SHOW",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            last_message_at=timezone.now(),
            open_loop="Live next step.",
            guardrails="Live guardrail.",
            last_handoff_note="Live handoff.",
        )

        self.demo_draft = BuddyDraft.objects.create(
            thread=self.demo_thread,
            reply_text="Fictief demo-antwoord.",
            intent="demo",
            tone="warm",
            risk_level=BuddyDraft.RiskLevel.LOW,
            requires_human_attention=True,
            state=BuddyDraft.State.DRAFTED,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

    def login_demo(self):
        self.client.force_login(self.demo_user)

    def test_demo_viewer_sees_only_marked_demo_threads(self):
        self.login_demo()

        response = self.client.get(reverse("chat-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Luna")
        self.assertContains(response, "DEMO-READONLY-THREAD")
        self.assertNotContains(response, "Live Creator")
        self.assertNotContains(response, "LIVE-THREAD-MUST-NOT-SHOW")
        self.assertTrue(response.context["demo_read_only"])
        self.assertEqual(
            response.context["access_state"]["status"],
            "readonly",
        )
        self.assertEqual(
            list(response.context["threads"]),
            [self.demo_thread],
        )

    def test_demo_chat_hides_write_controls_and_operational_navigation(self):
        self.login_demo()

        response = self.client.get(
            reverse("chat-hub"),
            {"thread": self.demo_thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Read-only demo view")
        self.assertContains(response, "Chats demo")
        self.assertNotContains(response, ">Creators<")
        self.assertNotContains(response, ">Channels<")
        self.assertNotContains(response, ">Assignments<")
        self.assertNotContains(response, ">Operators<")
        self.assertNotContains(response, ">Feeder<")
        self.assertContains(response, "Operator action")
        self.assertContains(response, "Trigger later")
        self.assertContains(response, "Save follow-up status")
        self.assertContains(response, "Save and open next")
        self.assertContains(
            response,
            "controls visible, changes blocked",
        )
        self.assertContains(
            response,
            'data-operator-status-options="v1"',
        )
        self.assertContains(response, "disabled")
        self.assertNotContains(
            response,
            "Close session & save handoff",
        )
        self.assertNotContains(response, "Create approval")
        self.assertNotContains(response, "New conversation thread")
        self.assertNotContains(response, "Mark as used")
        self.assertNotContains(response, "Edit thread")

    def test_demo_viewer_cannot_post_follow_up_or_handoff(self):
        self.login_demo()

        follow_up_response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "thread": self.demo_thread.pk,
                "follow_up_status": ThreadFollowUpStatus.Status.WARM,
                "follow_up_note": "Should never save.",
            },
        )
        self.assertEqual(follow_up_response.status_code, 403)
        self.assertFalse(
            ThreadFollowUpStatus.objects.filter(
                thread=self.demo_thread,
            ).exists()
        )

        original_open_loop = self.demo_thread.open_loop
        handoff_response = self.client.post(
            reverse("chat-hub"),
            {
                "thread": self.demo_thread.pk,
                "handoff_summary": "Should not save.",
                "next_step": "Should not save.",
                "close_signal": "overdracht_klaar",
            },
        )
        self.assertEqual(handoff_response.status_code, 403)

        self.demo_thread.refresh_from_db()
        self.assertEqual(self.demo_thread.open_loop, original_open_loop)

    def test_demo_viewer_cannot_create_approvals_or_approve_drafts(self):
        self.login_demo()

        approval_response = self.client.post(
            reverse("approval-create"),
            {
                "workspace": "chats",
                "thread": self.demo_thread.pk,
                "approval_type": Approval.Type.CONTENT_APPROVAL,
                "summary": "Should not save.",
            },
        )
        self.assertEqual(approval_response.status_code, 403)
        self.assertFalse(Approval.objects.exists())

        draft_response = self.client.post(
            reverse(
                "buddy-draft-approve",
                kwargs={"pk": self.demo_draft.pk},
            )
        )
        self.assertEqual(draft_response.status_code, 403)

        self.demo_draft.refresh_from_db()
        self.assertEqual(
            self.demo_draft.state,
            BuddyDraft.State.DRAFTED,
        )

    def test_demo_viewer_cannot_open_create_or_edit_forms(self):
        self.login_demo()

        create_response = self.client.get(
            reverse("conversation-thread-create")
        )
        edit_response = self.client.get(
            reverse(
                "conversation-thread-update",
                kwargs={"pk": self.demo_thread.pk},
            )
        )

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(edit_response.status_code, 403)

    def test_demo_viewer_can_open_demo_detail_but_not_live_detail(self):
        self.login_demo()

        demo_response = self.client.get(
            reverse(
                "conversation-thread-detail",
                kwargs={"pk": self.demo_thread.pk},
            )
        )
        live_response = self.client.get(
            reverse(
                "conversation-thread-detail",
                kwargs={"pk": self.live_thread.pk},
            )
        )

        self.assertEqual(demo_response.status_code, 200)
        self.assertContains(demo_response, "Read-only demo view")
        self.assertNotContains(demo_response, "Edit thread")
        self.assertNotContains(
            demo_response,
            "Approve draft",
        )
        self.assertEqual(live_response.status_code, 404)

    def test_demo_viewer_can_logout(self):
        self.login_demo()

        response = self.client.post(reverse("logout"))

        self.assertIn(response.status_code, {302, 303})

    def test_demo_login_landing_redirects_to_cockpit(self):
        self.login_demo()

        landing_response = self.client.get(
            reverse("operations-dashboard")
        )
        cockpit_response = self.client.get(
            reverse("adultadsuite-cockpit")
        )
        trigger_response = self.client.get(
            reverse("adultadsuite-triggers")
        )

        self.assertRedirects(
            landing_response,
            reverse("adultadsuite-cockpit"),
            fetch_redirect_response=False,
        )
        self.assertEqual(cockpit_response.status_code, 200)
        self.assertContains(cockpit_response, "Read-only demo")
        self.assertEqual(trigger_response.status_code, 200)

    def test_demo_viewer_cannot_open_operational_get_routes(self):
        self.login_demo()

        blocked_url_names = (
            "creator-list",
            "channel-list",
            "assignment-list",
            "operator-list",
            "feeder-hub",
            "conversation-thread-list",
            "conversation-thread-create",
        )

        for url_name in blocked_url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 403)

    def test_normal_operator_remains_writable(self):
        user_model = get_user_model()
        operator_user = user_model.objects.create_user(
            username="normal-operator",
            password="x",
            is_active=True,
        )
        operator = Operator.objects.create(user=operator_user)
        OperatorAssignment.objects.create(
            operator=operator,
            creator=self.live_creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=timezone.now(),
            active=True,
        )

        self.client.force_login(operator_user)
        response = self.client.get(
            reverse("chat-hub"),
            {"thread": self.live_thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Save follow-up status")
        self.assertContains(
            response,
            "Close session & save handoff",
        )
        self.assertFalse(response.context["demo_read_only"])


class DemoSeedCleanupTests(TestCase):
    def test_reset_removes_marker_matched_creator_after_display_name_change(self):
        renamed_demo = Creator.objects.create(
            display_name="Renamed Demo Creator",
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
            notes=DEMO_DATA_MARKER,
        )
        similar_but_not_demo = Creator.objects.create(
            display_name="Marker Lookalike",
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
            notes=f"prefix {DEMO_DATA_MARKER} suffix",
        )

        stdout = StringIO()

        call_command(
            "seed_buddy_demo_scenarios",
            "--reset",
            stdout=stdout,
        )

        self.assertFalse(
            Creator.objects.filter(pk=renamed_demo.pk).exists()
        )
        self.assertTrue(
            Creator.objects.filter(pk=similar_but_not_demo.pk).exists()
        )
        self.assertIn(
            "Removed 1 matching demo creator(s).",
            stdout.getvalue(),
        )
