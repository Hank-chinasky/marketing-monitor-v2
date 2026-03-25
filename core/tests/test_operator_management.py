from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Creator, Operator, OperatorAssignment


class OperatorManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.admin = User.objects.create_user(
            username="admin",
            password="x",
            is_active=True,
            is_staff=True,
        )

        self.operator_user = User.objects.create_user(
            username="operator",
            email="operator@example.com",
            password="x",
            first_name="Op",
            last_name="Erator",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)

        self.creator = Creator.objects.create(
            display_name="Creator One",
            legal_name="Creator One BV",
            status="active",
            consent_status="active",
            primary_operator=self.operator,
        )

        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope="full_management",
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=None,
            active=True,
        )

    def test_operator_list_requires_admin(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("operator-list"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_open_operator_list_and_sees_edit_actions(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("operator-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.operator_user.username)
        self.assertContains(response, reverse("operator-update", kwargs={"pk": self.operator.pk}))
        self.assertContains(
            response,
            reverse("operator-reset-password", kwargs={"pk": self.operator.pk}),
        )
        self.assertContains(
            response,
            reverse("operator-toggle-active", kwargs={"pk": self.operator.pk}),
        )
        self.assertContains(response, "Blokkeer")

    def test_admin_can_open_operator_update(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("operator-update", kwargs={"pk": self.operator.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operator bewerken")
        self.assertContains(response, self.operator_user.username)

    def test_admin_can_update_operator_profile(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("operator-update", kwargs={"pk": self.operator.pk}),
            data={
                "username": "operator-updated",
                "email": "updated@example.com",
                "first_name": "Updated",
                "last_name": "Name",
                "is_active": "on",
            },
        )
        self.assertRedirects(
            response,
            reverse("operator-update", kwargs={"pk": self.operator.pk}) + "?saved=1",
        )

        self.operator_user.refresh_from_db()
        self.assertEqual(self.operator_user.username, "operator-updated")
        self.assertEqual(self.operator_user.email, "updated@example.com")
        self.assertEqual(self.operator_user.first_name, "Updated")
        self.assertEqual(self.operator_user.last_name, "Name")
        self.assertTrue(self.operator_user.is_active)

    def test_admin_can_toggle_operator_active_status(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("operator-toggle-active", kwargs={"pk": self.operator.pk}),
            data={"next": reverse("operator-list")},
        )
        self.assertRedirects(
            response,
            reverse("operator-list") + "?status_changed=1&operator=operator",
        )

        self.operator_user.refresh_from_db()
        self.assertFalse(self.operator_user.is_active)

        response = self.client.post(
            reverse("operator-toggle-active", kwargs={"pk": self.operator.pk}),
            data={"next": reverse("operator-list")},
        )
        self.assertRedirects(
            response,
            reverse("operator-list") + "?status_changed=1&operator=operator",
        )

        self.operator_user.refresh_from_db()
        self.assertTrue(self.operator_user.is_active)

    def test_admin_can_reset_operator_password(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("operator-reset-password", kwargs={"pk": self.operator.pk}),
            data={
                "password1": "NieuwSterkWachtwoord123",
                "password2": "NieuwSterkWachtwoord123",
            },
        )
        self.assertRedirects(
            response,
            reverse("operator-reset-password", kwargs={"pk": self.operator.pk}) + "?saved=1",
        )

        self.operator_user.refresh_from_db()
        self.assertTrue(self.operator_user.check_password("NieuwSterkWachtwoord123"))

    def test_operator_create_page_has_real_back_button(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("operator-create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="secondary-button"')
        self.assertContains(response, "Terug naar operators")

    def test_creator_create_page_has_real_back_button(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("creator-create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="secondary-button"')
        self.assertContains(response, "Terug naar creators")

    def test_operator_list_shows_blocked_status_after_toggle(self):
        self.client.force_login(self.admin)

        self.client.post(
            reverse("operator-toggle-active", kwargs={"pk": self.operator.pk}),
            data={"next": reverse("operator-list")},
        )

        response = self.client.get(reverse("operator-list"))
        self.assertContains(response, "geblokkeerd")
        self.assertContains(response, "Deblokkeer")