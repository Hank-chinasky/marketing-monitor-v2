from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import (
    ConversationThread,
    Creator,
    CreatorChannel,
    Operator,
    OperatorAssignment,
)


class BuddySurfaceV0Tests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="buddy-surface-user",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.user)
        self.client.force_login(self.user)

        self.creator = Creator.objects.create(
            display_name="Buddy Surface Creator",
            legal_name="Buddy Surface Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="buddy-surface-channel",
            profile_url="https://example.com/buddy-surface-channel",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
        )
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=timezone.now() - timedelta(days=1),
            active=True,
        )
        self.thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_thread_id="buddy-surface-thread",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            open_loop="Pak de warme persoonlijke lijn op.",
            guardrails="Niet pushen zonder context.",
            risk_flags="",
            last_handoff_note="Gesprek niet resetten; toon is al opgebouwd.",
        )

    def assert_buddy_surface_present_and_safe(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buddy")
        self.assertContains(response, "Buddy status")
        self.assertContains(response, "Waarom nu")
        self.assertContains(response, "Laatste context")
        self.assertContains(response, "Open loop")
        self.assertContains(response, "Niet doen")
        self.assertContains(response, "Volgende stap")
        self.assertContains(response, "Betrouwbaarheid")
        self.assertContains(response, "Demo-context / menselijk checken")
        self.assertContains(response, "Geen generieke trigger sturen")

        html = response.content.decode()
        self.assertEqual(html.count('id="chat-buddy-context"'), 1)
        self.assertEqual(html.count("Buddy Context Surface"), 1)
        self.assertIn('data-chat-layout="messages-buddy"', html)
        self.assertLess(html.index("Berichten"), html.index("Buddy Context Surface"))
        self.assertNotIn("Buddy-slot", html)
        self.assertNotIn("Intern reply draft voorstel", html)
        self.assertIn(
            "grid-template-columns: minmax(0, 1fr) minmax(300px, 340px);",
            html,
        )
        self.assertIn("max-width: 1600px;", html)
        self.assertIn('"context work"', html)
        self.assertIn('". operations"', html)
        self.assertNotIn('"operations operations"', html)
        self.assertIn("chat-sticky-context", html)
        self.assertIn(".chat-sticky-context {", html)
        self.assertIn("@media (min-width: 1101px)", html)
        self.assertIn("position: sticky;", html)
        self.assertIn("align-self: stretch;", html)
        self.assertIn('"messages buddy"', html)
        self.assertIn('"followup buddy"', html)
        self.assertIn("chat-follow-up-panel", html)
        self.assertLess(
            html.index("Buddy Context Surface"),
            html.index("Follow-up status"),
        )
        self.assertIn("@media (max-width: 1100px)", html)
        self.assertIn("@media (max-width: 720px)", html)
        self.assertIn("Context & veiligheid", html)
        self.assertIn("Operationele details", html)
        self.assertIn("Templates v1", html)
        self.assertIn("Sessie & overdracht", html)
        self.assertNotIn(
            "grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);",
            html,
        )
        self.assertNotIn("Verstuur nu", html)
        self.assertNotIn("bulk verzenden", html)
        self.assertNotIn("sendtrigger", html)
        self.assertNotIn("trigger-send", html)
        self.assertNotIn('action="/mara/', html)
        self.assertNotIn("cashflow.adultadsuite.com", html)
        self.assertNotIn("php artisan", html)

    def test_chats_normal_mode_shows_compact_buddy_surface(self):
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assert_buddy_surface_present_and_safe(response)

    def test_chats_focus_mode_shows_compact_buddy_surface(self):
        response = self.client.get(
            reverse("chat-hub"),
            {"focus": "1", "thread": self.thread.pk},
        )

        self.assert_buddy_surface_present_and_safe(response)
