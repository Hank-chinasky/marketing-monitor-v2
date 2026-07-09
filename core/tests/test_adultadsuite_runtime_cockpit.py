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
        self.assertContains(response, "Mara elke dag meer omzet")
        self.assertContains(response, "Vandaag eerst")
        self.assertContains(response, "placeholders")
        self.assertContains(response, "geen live imports")
        self.assertContains(response, "CreatorWorkboardFlow")
        self.assertContains(response, "De live werkvloer binnen AdultAdSuite")
        self.assertContains(response, "Open normale werkvloer")
        self.assertContains(response, "Open focusstand")
        self.assertContains(response, "Focusstand")
        self.assertContains(response, "focus=1")
        self.assertContains(response, "Gebruik de normale werkvloer voor overzicht en statusbeheer")
        self.assertContains(response, "Gebruik focusstand voor bewust opvolgen en schrijven")
        self.assertContains(response, "Status: live route beschikbaar")
        self.assertContains(response, "Trigger Radar")
        self.assertContains(response, "Klantenstatus")
        self.assertContains(response, "Revenue / Bestellingen")
        self.assertContains(response, "Mail Health")
        self.assertContains(response, "Campagnes")
        self.assertContains(response, "Funnels / Landingspagina")
        self.assertContains(response, "App / Flowmatch")
        self.assertContains(response, "Data Health / Source Reliability")
        self.assertContains(response, "Safety boundary")
        self.assertContains(response, "geen mail sends")
        self.assertContains(response, "geen chat sends")
        self.assertContains(
            response,
            "Cashflow is een module of legacybron binnen AdultAdSuite, niet de hoofdtool",
        )
