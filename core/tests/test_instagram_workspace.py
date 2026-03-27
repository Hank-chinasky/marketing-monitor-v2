from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Creator, CreatorChannel, CreatorMaterial, Operator, OperatorAssignment


class InstagramWorkspaceViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin-workspace",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_user = User.objects.create_user(
            username="operator-workspace",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)

        self.other_operator_user = User.objects.create_user(
            username="other-operator-workspace",
            password="x",
            is_active=True,
        )
        self.other_operator = Operator.objects.create(user=self.other_operator_user)

        self.creator = Creator.objects.create(
            display_name="Workspace Creator",
            legal_name="Workspace Creator BV",
            status="active",
            consent_status="active",
            primary_link="https://example.com/landing",
            content_source_type="shared_drive",
            content_source_url="https://drive.example.com/folder",
            content_ready_status="ready_to_post",
        )
        self.instagram_channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform="instagram",
            handle="workspace-instagram",
            profile_url="https://instagram.com/workspace-instagram",
            status="active",
            access_mode="operator_direct",
            recovery_owner="creator",
            credential_status="known",
            login_identifier="workspace@login",
            two_factor_enabled=True,
            last_operator_update="Laatste contextregel",
            last_operator_update_at=timezone.now(),
        )
        self.tiktok_channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform="tiktok",
            handle="workspace-tiktok",
            status="active",
            access_mode="operator_direct",
            recovery_owner="creator",
            credential_status="known",
        )
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope="full_management",
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=None,
            active=True,
        )
        CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.admin,
            label="Workspace image",
            file=SimpleUploadedFile("workspace.jpg", b"image-bytes", content_type="image/jpeg"),
        )

    def test_admin_can_open_instagram_workspace(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("instagram-workspace", kwargs={"pk": self.instagram_channel.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Instagram Workspace")
        self.assertContains(response, self.creator.display_name)

    def test_scoped_operator_can_open_instagram_workspace(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("instagram-workspace", kwargs={"pk": self.instagram_channel.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.creator.primary_link)
        self.assertContains(response, "Laatste contextregel")
        self.assertContains(response, "Workspace image")

    def test_unscoped_operator_gets_404_for_instagram_workspace(self):
        self.client.force_login(self.other_operator_user)
        response = self.client.get(reverse("instagram-workspace", kwargs={"pk": self.instagram_channel.pk}))
        self.assertEqual(response.status_code, 404)

    def test_non_instagram_channel_gets_404_for_workspace_route(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("instagram-workspace", kwargs={"pk": self.tiktok_channel.pk}))
        self.assertEqual(response.status_code, 404)

    def test_channel_detail_shows_workspace_link_only_for_instagram(self):
        self.client.force_login(self.admin)
        instagram_response = self.client.get(reverse("channel-detail", kwargs={"pk": self.instagram_channel.pk}))
        tiktok_response = self.client.get(reverse("channel-detail", kwargs={"pk": self.tiktok_channel.pk}))

        self.assertContains(
            instagram_response,
            reverse("instagram-workspace", kwargs={"pk": self.instagram_channel.pk}),
        )
        self.assertNotContains(tiktok_response, "Open Workspace")
