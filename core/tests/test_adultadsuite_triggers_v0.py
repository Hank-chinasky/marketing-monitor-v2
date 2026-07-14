from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdultAdSuiteTriggersV0Tests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="trigger-preview-user",
            password="x",
            is_active=True,
        )
        self.client.force_login(self.user)

    def test_adultadsuite_triggers_preview_page_renders_queue(self):
        response = self.client.get(reverse("adultadsuite-triggers"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AdultAdSuite")
        self.assertContains(response, "TriggerModule")
        self.assertContains(response, "Trigger wachtrij")
        self.assertContains(response, "Preview-only v0")
        self.assertContains(response, "trigger-card urgent")
        self.assertContains(response, "trigger-card warm")
        self.assertContains(response, "trigger-card ready")
        self.assertContains(response, "trigger-card info")
        self.assertContains(response, "trigger-card cooldown")
        self.assertContains(response, "trigger-card vip")
        self.assertContains(response, "Jessica Demo")
        self.assertContains(response, "Warm profiel")
        self.assertContains(response, "Cooldown voorbeeld")
        self.assertContains(response, "VIP koper")
        self.assertContains(response, "Datakwaliteit voorbeeld")
        self.assertContains(response, "Buddy")
        self.assertContains(response, "Buddy status")
        self.assertContains(response, "Waarom nu")
        self.assertContains(response, "Laatste context")
        self.assertContains(response, "Open loop")
        self.assertContains(response, "Niet doen")
        self.assertContains(response, "Volgende stap")
        self.assertContains(response, "Betrouwbaarheid")
        self.assertContains(response, "Geen generieke trigger sturen")
        self.assertContains(response, reverse("chat-hub"))

        html = response.content.decode()
        self.assertGreaterEqual(html.count("Buddy status"), 6)

    def test_adultadsuite_triggers_preview_page_has_no_live_send_or_legacy_hooks(self):
        response = self.client.get(reverse("adultadsuite-triggers"))
        html = response.content.decode()

        self.assertNotIn('action="/mara/', html)
        self.assertNotIn("cashflow.adultadsuite.com/mara/trigger", html)
        self.assertNotIn("php artisan", html)
        self.assertNotIn("Verstuur nu", html)
        self.assertNotIn("bulk verzenden", html)
        self.assertNotIn("bulk-send", html)
        self.assertNotIn("sendtrigger", html)
        self.assertNotIn("trigger-send", html)
        self.assertNotIn("triggerqueue", html)
        self.assertNotIn("live-send", html)

    def test_adultadsuite_triggers_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse("adultadsuite-triggers"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])
