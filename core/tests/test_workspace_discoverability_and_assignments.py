from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Creator, CreatorChannel, Operator, OperatorAssignment


class CreatorDetailWorkspaceLinksTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin-discoverability",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.analytics_user = user_model.objects.create_user(
            username="analytics-discoverability",
            password="x",
            is_active=True,
        )
        self.analytics_operator = Operator.objects.create(user=self.analytics_user)

        self.creator = Creator.objects.create(
            display_name="Discoverability Creator",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.instagram_channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="discover-instagram",
            profile_url="https://instagram.com/discover-instagram",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.CREATOR,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
        )
        self.tiktok_channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.TIKTOK,
            handle="discover-tiktok",
            profile_url="https://tiktok.com/@discover-tiktok",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.CREATOR,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
        )
        OperatorAssignment.objects.create(
            operator=self.analytics_operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.ANALYTICS_ONLY,
            starts_at=timezone.now() - timedelta(days=1),
            active=True,
        )

    def test_admin_sees_workspace_link_on_creator_detail_for_instagram_channel(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("channel-detail", kwargs={"pk": self.instagram_channel.pk}))
        self.assertContains(response, reverse("instagram-workspace", kwargs={"pk": self.instagram_channel.pk}))
        self.assertNotContains(response, reverse("instagram-workspace", kwargs={"pk": self.tiktok_channel.pk}))

    def test_analytics_only_operator_does_not_get_workspace_link_on_creator_detail(self):
        self.client.force_login(self.analytics_user)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("channel-detail", kwargs={"pk": self.instagram_channel.pk}))
        self.assertNotContains(response, reverse("instagram-workspace", kwargs={"pk": self.instagram_channel.pk}))


class AssignmentManagementViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin-assignments-ui",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_user = user_model.objects.create_user(
            username="operator-assignments-ui",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)
        self.creator = Creator.objects.create(
            display_name="Assignment Creator",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.assignment = OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=timezone.now() - timedelta(days=1),
            active=True,
        )

    def test_assignment_list_shows_management_actions_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("assignment-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("assignment-create"))
        self.assertContains(response, reverse("assignment-update", kwargs={"pk": self.assignment.pk}))
        self.assertContains(response, reverse("assignment-deactivate", kwargs={"pk": self.assignment.pk}))

    def test_assignment_list_shows_reactivate_for_inactive_assignment(self):
        self.assignment.active = False
        self.assignment.save(update_fields=["active"])

        self.client.force_login(self.admin)
        response = self.client.get(reverse("assignment-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("assignment-reactivate", kwargs={"pk": self.assignment.pk}))
        self.assertNotContains(response, reverse("assignment-deactivate", kwargs={"pk": self.assignment.pk}))

    def test_admin_can_deactivate_assignment(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("assignment-deactivate", kwargs={"pk": self.assignment.pk}))
        self.assertEqual(response.status_code, 302)
        self.assignment.refresh_from_db()
        self.assertFalse(self.assignment.active)

    def test_admin_can_reactivate_assignment(self):
        self.assignment.active = False
        self.assignment.save(update_fields=["active"])

        self.client.force_login(self.admin)
        response = self.client.post(reverse("assignment-reactivate", kwargs={"pk": self.assignment.pk}))

        self.assertEqual(response.status_code, 302)
        self.assignment.refresh_from_db()
        self.assertTrue(self.assignment.active)

    def test_non_admin_cannot_deactivate_assignment(self):
        self.client.force_login(self.operator_user)
        response = self.client.post(reverse("assignment-deactivate", kwargs={"pk": self.assignment.pk}))
        self.assertEqual(response.status_code, 403)

    def test_non_admin_cannot_reactivate_assignment(self):
        self.assignment.active = False
        self.assignment.save(update_fields=["active"])

        self.client.force_login(self.operator_user)
        response = self.client.post(reverse("assignment-reactivate", kwargs={"pk": self.assignment.pk}))

        self.assertEqual(response.status_code, 403)