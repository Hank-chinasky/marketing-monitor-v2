from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.forms import CreatorForm
from core.models import Creator, CreatorChannel, Operator, OperatorAssignment


class ValidationAndViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="admin2", password="x", is_staff=True, is_active=True)
        self.operator_user = User.objects.create_user(username="operator2", password="x", is_active=True)
        self.operator = Operator.objects.create(user=self.operator_user)
        self.creator = Creator.objects.create(display_name="Creator A", status="active", consent_status="active")

    def test_creator_status_consent_invalid_object_and_form(self):
        creator = Creator(display_name="Invalid", status="active", consent_status="pending")
        with self.assertRaises(ValidationError):
            creator.full_clean()

        form = CreatorForm(
            data={
                "display_name": "Invalid",
                "legal_name": "",
                "status": "active",
                "consent_status": "pending",
                "primary_operator": "",
                "notes": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("consent_status", form.errors)

    def test_channel_platform_handle_case_insensitive_unique(self):
        CreatorChannel.objects.create(
            creator=self.creator,
            platform="tiktok",
            handle="MyHandle",
            status="active",
            access_mode="creator_only",
            recovery_owner="creator",
        )
        dupe = CreatorChannel(
            creator=self.creator,
            platform="tiktok",
            handle="myhandle",
            status="active",
            access_mode="creator_only",
            recovery_owner="creator",
        )
        with self.assertRaises(ValidationError):
            dupe.full_clean()

    def test_admin_only_mixin_blocks_operator_for_creator_update(self):
        self.client.login(username="operator2", password="x")
        response = self.client.get(reverse("creator-update", kwargs={"pk": self.creator.pk}))
        self.assertEqual(response.status_code, 403)

    def test_overlap_per_creator_across_operators_blocked(self):
        user2 = get_user_model().objects.create_user(username="operator3", password="x", is_active=True)
        op2 = Operator.objects.create(user=user2)
        now = timezone.now()

        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            starts_at=now - timedelta(days=1),
            ends_at=None,
            active=True,
        )
        second = OperatorAssignment(
            operator=op2,
            creator=self.creator,
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(days=1),
            active=True,
        )
        with self.assertRaises(ValidationError):
            second.full_clean()
