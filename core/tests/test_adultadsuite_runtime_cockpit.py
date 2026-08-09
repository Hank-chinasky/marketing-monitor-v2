from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdultAdSuiteRuntimeCockpitTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="adultadsuite-user",
            password="x",
            is_active=True,
        )

    def test_adultadsuite_cockpit_requires_login(self):
        response = self.client.get(reverse("adultadsuite-cockpit"))

        self.assertIn(response.status_code, [302, 401, 403])
        if response.status_code == 302:
            self.assertIn("/login/", response["Location"])

    def test_adultadsuite_cockpit_renders_revenue_day_plan_for_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("adultadsuite-cockpit"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AdultAdSuite Runtime Cockpit")
        self.assertContains(response, "/chats/")
        self.assertContains(response, "Revenue Day Plan")
        self.assertContains(response, "Help the operator generate more revenue")
        self.assertContains(response, "Today first")
        self.assertContains(response, "placeholders")
        self.assertContains(response, "no live imports")
        self.assertContains(response, "CreatorWorkboardFlow")
        self.assertContains(response, "The live work floor inside AdultAdSuite")
        self.assertContains(response, "Open CreatorWorkboardFlow")
        self.assertNotContains(response, "Open focus mode")
        self.assertNotContains(response, "?focus=1")
        self.assertNotContains(response, "Focus mode")
        self.assertNotContains(response, "focus=1")
        self.assertContains(response, "live operator work floor inside AdultAdSuite")
        self.assertContains(response, "continue directly to the next.")
        self.assertContains(response, "Status: live route available")
        self.assertContains(response, "Trigger Radar")
        self.assertContains(response, "Customer status")
        self.assertContains(response, "Revenue / Orders")
        self.assertContains(response, "Mail Health")
        self.assertContains(response, "Campaigns")
        self.assertContains(response, "Funnels / Landing pages")
        self.assertContains(response, "App / Flowmatch")
        self.assertContains(response, "Data Health / Source Reliability")
        self.assertContains(response, "Safety boundary")
        self.assertContains(response, "No live imports")
        self.assertContains(response, "mail sends")
        self.assertContains(response, "chat sends")
        self.assertContains(
            response,
            "Cashflow is a module or legacy source inside AdultAdSuite, not the primary tool",
        )
