from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.forms import CreatorChannelForm
from core.models import Creator, CreatorChannel, Operator, OperatorAssignment


class InstagramWorkspaceSessionDisciplineTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.admin_user = user_model.objects.create_user(
            username="workspace-admin",
            password="testpass123",
            is_active=True,
            is_staff=True,
        )

        self.posting_user = user_model.objects.create_user(
            username="workspace-posting",
            password="testpass123",
            is_active=True,
        )
        self.posting_operator = Operator.objects.create(user=self.posting_user)

        self.analytics_user = user_model.objects.create_user(
            username="workspace-analytics",
            password="testpass123",
            is_active=True,
        )
        self.analytics_operator = Operator.objects.create(user=self.analytics_user)

        self.other_user = user_model.objects.create_user(
            username="workspace-other",
            password="testpass123",
            is_active=True,
        )
        self.other_operator = Operator.objects.create(user=self.other_user)

        self.creator = Creator.objects.create(
            display_name="Creator One",
            legal_name="Creator One BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            primary_operator=self.posting_operator,
            primary_link="https://example.com/primary-link",
            content_source_type=Creator.ContentSourceType.SHARED_DRIVE,
            content_source_url="https://drive.example.com/source",
            content_ready_status=Creator.ContentReadyStatus.READY_TO_POST,
        )

        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="creator-one",
            profile_url="https://instagram.com/creator-one",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.CREATOR,
            login_identifier="creator-login@example.com",
            credential_status=CreatorChannel.CredentialStatus.NEEDS_RESET,
            access_notes="Use approved flow only.",
            two_factor_enabled=False,
            vpn_required=True,
            approved_egress_ip="",
            approved_ip_label="",
            approved_access_region="",
            access_profile_notes="Review disclosure notes before action.",
        )

        starts_at = timezone.now() - timedelta(days=1)

        OperatorAssignment.objects.create(
            operator=self.posting_operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.POSTING_ONLY,
            starts_at=starts_at,
            active=True,
        )

        OperatorAssignment.objects.create(
            operator=self.analytics_operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.ANALYTICS_ONLY,
            starts_at=starts_at,
            active=True,
        )

        self.workspace_url = reverse("instagram-workspace", kwargs={"pk": self.channel.pk})

    def test_invalid_session_form_requires_structured_fields(self):
        self.client.force_login(self.posting_user)

        response = self.client.post(
            self.workspace_url,
            {
                "session_blockers": "Nog geen toegang tot stories.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response,
            "handoff_form",
            "session_what_done",
            "Dit veld is verplicht.",
        )
        self.assertFormError(
            response,
            "handoff_form",
            "session_next_action",
            "Dit veld is verplicht.",
        )
        self.assertFormError(
            response,
            "handoff_form",
            "session_policy_context_reviewed",
            "Dit veld is verplicht.",
        )

        self.channel.refresh_from_db()
        self.assertEqual(self.channel.session_what_done, "")
        self.assertEqual(self.channel.session_next_action, "")
        self.assertFalse(self.channel.session_policy_context_reviewed)
        self.assertIsNone(self.channel.session_updated_at)
        self.assertEqual(self.channel.last_operator_update, "")

    def test_posting_only_operator_can_save_structured_session(self):
        self.client.force_login(self.posting_user)

        response = self.client.post(
            self.workspace_url,
            {
                "session_what_done": "Instagram profiel gecontroleerd en bio-link bijgewerkt.",
                "session_next_action": "Stories publiceren na approval.",
                "session_blockers": "Stories approval ontbreekt nog.",
                "session_policy_context_reviewed": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Workspace session opgeslagen.")
        self.assertContains(response, "Instagram profiel gecontroleerd en bio-link bijgewerkt.")
        self.assertContains(response, "Stories publiceren na approval.")
        self.assertContains(response, "Stories approval ontbreekt nog.")

        self.channel.refresh_from_db()
        self.assertEqual(
            self.channel.session_what_done,
            "Instagram profiel gecontroleerd en bio-link bijgewerkt.",
        )
        self.assertEqual(self.channel.session_next_action, "Stories publiceren na approval.")
        self.assertEqual(self.channel.session_blockers, "Stories approval ontbreekt nog.")
        self.assertTrue(self.channel.session_policy_context_reviewed)
        self.assertIsNotNone(self.channel.session_updated_at)
        self.assertEqual(self.channel.last_operator_update_at, self.channel.session_updated_at)

    def test_last_operator_update_is_derived_from_structured_session(self):
        self.client.force_login(self.posting_user)

        self.client.post(
            self.workspace_url,
            {
                "session_what_done": "Linktree en profieltekst aangepast.",
                "session_next_action": "Nieuwe caption klaarzetten.",
                "session_blockers": "",
                "session_policy_context_reviewed": "on",
            },
        )

        self.channel.refresh_from_db()
        self.assertIn("Wat gedaan:\nLinktree en profieltekst aangepast.", self.channel.last_operator_update)
        self.assertIn("Next action:\nNieuwe caption klaarzetten.", self.channel.last_operator_update)
        self.assertIn("Blockers / open issues:\n-", self.channel.last_operator_update)
        self.assertIn(
            "Policy/disclosure context reviewed: Ja",
            self.channel.last_operator_update,
        )

    def test_workspace_shows_latest_session_context(self):
        timestamp = timezone.now()
        update_fields = self.channel.apply_workspace_session(
            what_done="Kanaal geopend en creatorcontext doorgenomen.",
            next_action="Caption finaliseren.",
            blockers="Nog geen finale media.",
            policy_context_reviewed=True,
            updated_at=timestamp,
        )
        self.channel.save(update_fields=update_fields)

        self.client.force_login(self.posting_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laatste sessiecontext")
        self.assertContains(response, "Kanaal geopend en creatorcontext doorgenomen.")
        self.assertContains(response, "Caption finaliseren.")
        self.assertContains(response, "Nog geen finale media.")
        self.assertContains(response, "Ja")

    def test_workspace_shows_policy_and_risk_signals(self):
        self.creator.primary_link = ""
        self.creator.save(update_fields=["primary_link"])

        self.client.force_login(self.posting_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "review required")
        self.assertContains(response, "Missing primary link")
        self.assertContains(response, "No 2FA enabled")
        self.assertContains(response, "Policy gap")
        self.assertContains(response, "Missing structured session handoff")
        self.assertContains(response, "Credential issue")

    def test_channel_edit_form_no_longer_exposes_legacy_handoff_fields(self):
        form = CreatorChannelForm(instance=self.channel)

        self.assertNotIn("last_operator_update", form.fields)
        self.assertNotIn("last_operator_update_at", form.fields)

    def test_admin_can_still_access_workspace(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Instagram Workspace / creator-one")

    def test_analytics_only_operator_gets_404(self):
        self.client.force_login(self.analytics_user)

        response = self.client.get(self.workspace_url)
        self.assertEqual(response.status_code, 404)

        post_response = self.client.post(
            self.workspace_url,
            {
                "session_what_done": "Analyse gedaan.",
                "session_next_action": "Niets",
                "session_policy_context_reviewed": "on",
            },
        )
        self.assertEqual(post_response.status_code, 404)

    def test_unassigned_operator_gets_404(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 404)