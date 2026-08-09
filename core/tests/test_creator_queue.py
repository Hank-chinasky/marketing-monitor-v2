from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Creator, CreatorChannel, Operator, OperatorAssignment


class CreatorQueueTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="creator-queue-admin",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_user = user_model.objects.create_user(
            username="creator-queue-operator",
            password="x",
            is_active=True,
        )
        self.other_operator_user = user_model.objects.create_user(
            username="creator-queue-other-operator",
            password="x",
            is_active=True,
        )
        self.unassigned_operator_user = user_model.objects.create_user(
            username="creator-queue-unassigned-operator",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)
        self.other_operator = Operator.objects.create(user=self.other_operator_user)
        Operator.objects.create(user=self.unassigned_operator_user)

        self.calm_creator = Creator.objects.create(
            display_name="Calm Creator",
            legal_name="Calm Legal Name",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            primary_operator=self.operator,
            content_ready_status=Creator.ContentReadyStatus.READY_TO_POST,
        )
        self.attention_creator = Creator.objects.create(
            display_name="Attention Creator",
            status=Creator.Status.PAUSED,
            consent_status=Creator.ConsentStatus.PENDING,
            content_ready_status=Creator.ContentReadyStatus.BLOCKED,
        )
        self.out_of_scope_creator = Creator.objects.create(
            display_name="Other Operator Creator",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            primary_operator=self.other_operator,
            content_ready_status=Creator.ContentReadyStatus.READY_TO_POST,
        )

        now = timezone.now()
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.calm_creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=now - timedelta(days=1),
            active=True,
        )
        OperatorAssignment.objects.create(
            operator=self.other_operator,
            creator=self.out_of_scope_creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=now - timedelta(days=1),
            active=True,
        )

        self.make_healthy_channel(
            creator=self.calm_creator,
            handle="calm-creator",
            updated_at=now,
        )
        self.make_healthy_channel(
            creator=self.out_of_scope_creator,
            handle="other-creator",
            updated_at=now,
        )

    @staticmethod
    def make_healthy_channel(creator, handle, updated_at):
        return CreatorChannel.objects.create(
            creator=creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle=handle,
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            login_identifier=f"{handle}@example.test",
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
            last_operator_update="Workflow is bijgewerkt.",
            last_operator_update_at=updated_at,
        )

    def test_admin_queue_renders_rows_summaries_and_default_attention_preset(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("creator-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["total_creators"], 3)
        self.assertEqual(response.context["summary"]["attention_count"], 1)
        self.assertEqual(response.context["summary"]["unassigned_count"], 1)
        self.assertEqual(response.context["visible_count"], 1)
        self.assertEqual(response.context["active_preset"], "attention")
        self.assertContains(response, "Attention Creator")
        self.assertContains(response, "Confirm or restore the consent status.")
        self.assertNotContains(response, "Calm Creator")

    def test_all_preset_renders_every_creator_in_admin_scope(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("creator-list"), {"preset": "all"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["visible_count"], 3)
        self.assertContains(response, "Calm Creator")
        self.assertContains(response, "Attention Creator")
        self.assertContains(response, "Other Operator Creator")
        self.assertNotContains(response, "No creators visible")

    def test_operator_queue_only_renders_creators_in_active_assignment_scope(self):
        self.client.force_login(self.operator_user)

        response = self.client.get(reverse("creator-list"), {"preset": "all"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["total_creators"], 1)
        self.assertContains(response, "Calm Creator")
        self.assertNotContains(response, "Attention Creator")
        self.assertNotContains(response, "Other Operator Creator")

    def test_search_and_field_filters_narrow_the_queue(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("creator-list"),
            {
                "preset": "all",
                "q": "Calm Legal",
                "status": Creator.Status.ACTIVE,
                "consent_status": Creator.ConsentStatus.ACTIVE,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["visible_count"], 1)
        self.assertContains(response, "Calm Creator")
        self.assertNotContains(response, "Attention Creator")
        self.assertNotContains(response, "Other Operator Creator")

    def test_operator_without_assignments_gets_safe_empty_queue(self):
        self.client.force_login(self.unassigned_operator_user)

        response = self.client.get(reverse("creator-list"), {"preset": "all"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["total_creators"], 0)
        self.assertEqual(response.context["visible_count"], 0)
        self.assertContains(response, "No creators visible")
