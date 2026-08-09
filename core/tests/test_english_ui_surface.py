from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class EnglishUISurfaceTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="english-ui-admin",
            password="x",
            is_active=True,
            is_staff=True,
        )

    def test_application_language_and_login_surface_are_english(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(settings.LANGUAGE_CODE, "en")
        self.assertContains(response, '<html lang="en">')
        self.assertContains(response, "Sign in")
        self.assertNotContains(response, "Inloggen")

    def test_core_demo_surfaces_use_english_navigation_and_labels(self):
        self.client.force_login(self.admin)

        dashboard = self.client.get(reverse("operations-dashboard"))
        creator_queue = self.client.get(reverse("creator-list"))

        self.assertContains(dashboard, "Operations Dashboard")
        self.assertContains(dashboard, "Quick actions")
        self.assertContains(creator_queue, "Creator operations queue")
        self.assertContains(creator_queue, "Quick filters")
        self.assertNotContains(dashboard, "Snelle acties")
        self.assertNotContains(creator_queue, "Operationele creators queue")
