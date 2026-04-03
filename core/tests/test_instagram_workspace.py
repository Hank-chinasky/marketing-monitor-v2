from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Creator, CreatorChannel, Operator, OperatorAssignment


class InstagramWorkspaceViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.admin_user = user_model.objects.create_user(
            username="admin-user",
            password="testpass123",
            is_active=True,
            is_staff=True,
        )

        self.full_management_user = user_model.objects.create_user(
            username="full-management-user",
            password="testpass123",
            is_active=True,
        )
        self.full_management_operator = Operator.objects.create(
            user=self.full_management_user
        )

        self.posting_only_user = user_model.objects.create_user(
            username="posting-only-user",
            password="testpass123",
            is_active=True,
        )
        self.posting_only_operator = Operator.objects.create(user=self.posting_only_user)

        self.analytics_only_user = user_model.objects.create_user(
            username="analytics-only-user",
            password="testpass123",
            is_active=True,
        )
        self.analytics_only_operator = Operator.objects.create(
            user=self.analytics_only_user
        )

        self.draft_only_user = user_model.objects.create_user(
            username="draft-only-user",
            password="testpass123",
            is_active=True,
        )
        self.draft_only_operator = Operator.objects.create(user=self.draft_only_user)

        self.creator = Creator.objects.create(
            display_name="Workspace Creator",
            legal_name="Workspace Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            primary_operator=self.posting_only_operator,
            primary_link="https://example.com/primary-link",
            content_source_type=Creator.ContentSourceType.SHARED_DRIVE,
            content_source_url="https://drive.example.com/source",
            content_ready_status=Creator.ContentReadyStatus.READY_TO_POST,
        )

        self.instagram_channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="workspace-instagram",
            profile_url="https://instagram.com/workspace-instagram",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.CREATOR,
            login_identifier="workspace@example.com",
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            access_notes="Gebruik de standaard policy.",
            two_factor_enabled=True,
            vpn_required=False,
            access_profile_notes="Disclosure vooraf bekijken.",
        )

        self.tiktok_channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.TIKTOK,
            handle="workspace-tiktok",
            profile_url="https://tiktok.com/@workspace-tiktok",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.CREATOR,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
            vpn_required=False,
        )

        starts_at = timezone.now() - timedelta(days=1)

        OperatorAssignment.objects.create(
            operator=self.full_management_operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=starts_at,
            active=True,
        )
        OperatorAssignment.objects.create(
            operator=self.posting_only_operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.POSTING_ONLY,
            starts_at=starts_at,
            active=True,
        )
        OperatorAssignment.objects.create(
            operator=self.analytics_only_operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.ANALYTICS_ONLY,
            starts_at=starts_at,
            active=True,
        )
        OperatorAssignment.objects.create(
            operator=self.draft_only_operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.DRAFT_ONLY,
            starts_at=starts_at,
            active=True,
        )

        self.workspace_url = reverse(
            "instagram-workspace",
            kwargs={"pk": self.instagram_channel.pk},
        )
        self.tiktok_workspace_url = reverse(
            "instagram-workspace",
            kwargs={"pk": self.tiktok_channel.pk},
        )
        self.channel_detail_url = reverse(
            "channel-detail",
            kwargs={"pk": self.instagram_channel.pk},
        )
        self.tiktok_channel_detail_url = reverse(
            "channel-detail",
            kwargs={"pk": self.tiktok_channel.pk},
        )

    def test_admin_can_open_instagram_workspace(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Instagram Workspace / workspace-instagram")

    def test_admin_can_save_handoff_in_workspace(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            self.workspace_url,
            {
                "session_what_done": "Bio en link gecontroleerd.",
                "session_next_action": "Caption klaarzetten voor morgen.",
                "session_blockers": "Nog geen nieuwe visual.",
                "session_policy_context_reviewed": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Workspace session opgeslagen.")

        self.instagram_channel.refresh_from_db()
        self.assertEqual(self.instagram_channel.session_what_done, "Bio en link gecontroleerd.")
        self.assertEqual(
            self.instagram_channel.session_next_action,
            "Caption klaarzetten voor morgen.",
        )
        self.assertEqual(self.instagram_channel.session_blockers, "Nog geen nieuwe visual.")
        self.assertTrue(self.instagram_channel.session_policy_context_reviewed)

    def test_posting_only_operator_can_open_instagram_workspace(self):
        self.client.force_login(self.posting_only_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Instagram Workspace / workspace-instagram")

    def test_posting_only_operator_can_save_handoff_in_workspace(self):
        self.client.force_login(self.posting_only_user)
        response = self.client.post(
            self.workspace_url,
            {
                "session_what_done": "Caption aangepast en profiel gecheckt.",
                "session_next_action": "Story later vandaag live zetten.",
                "session_blockers": "",
                "session_policy_context_reviewed": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Workspace session opgeslagen.")

        self.instagram_channel.refresh_from_db()
        self.assertEqual(
            self.instagram_channel.session_what_done,
            "Caption aangepast en profiel gecheckt.",
        )
        self.assertEqual(
            self.instagram_channel.session_next_action,
            "Story later vandaag live zetten.",
        )
        self.assertEqual(self.instagram_channel.session_blockers, "")
        self.assertTrue(self.instagram_channel.session_policy_context_reviewed)
        self.assertIn("Wat gedaan:", self.instagram_channel.last_operator_update)

    def test_full_management_operator_can_open_instagram_workspace(self):
        self.client.force_login(self.full_management_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Instagram Workspace / workspace-instagram")

    def test_analytics_only_operator_gets_404_for_instagram_workspace(self):
        self.client.force_login(self.analytics_only_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 404)

    def test_analytics_only_operator_cannot_save_handoff_in_workspace(self):
        self.client.force_login(self.analytics_only_user)
        response = self.client.post(
            self.workspace_url,
            {
                "session_what_done": "Analyse gedaan.",
                "session_next_action": "Niets",
                "session_policy_context_reviewed": "on",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_draft_only_operator_gets_404_for_instagram_workspace(self):
        self.client.force_login(self.draft_only_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 404)

    def test_non_instagram_channel_gets_404_for_workspace_route(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.tiktok_workspace_url)

        self.assertEqual(response.status_code, 404)

    def test_channel_detail_shows_workspace_link_for_allowed_workspace_scope(self):
        self.client.force_login(self.posting_only_user)
        response = self.client.get(self.channel_detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.workspace_url)

    def test_channel_detail_hides_workspace_link_for_disallowed_workspace_scope(self):
        self.client.force_login(self.analytics_only_user)
        response = self.client.get(self.channel_detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.workspace_url)

    def test_channel_detail_shows_workspace_link_only_for_instagram(self):
        self.client.force_login(self.posting_only_user)
        response = self.client.get(self.tiktok_channel_detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("instagram-workspace", kwargs={"pk": self.tiktok_channel.pk}),
        )

    def test_channel_detail_renders_workspace_as_primary_action(self):
        self.client.force_login(self.posting_only_user)
        response = self.client.get(self.channel_detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.workspace_url)

    def test_channel_detail_keeps_back_links_as_quick_links(self):
        self.client.force_login(self.posting_only_user)
        response = self.client.get(self.workspace_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("channel-detail", kwargs={"pk": self.instagram_channel.pk}))