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
    ThreadFollowUpStatus,
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
            thread_summary=(
                "Warme persoonlijke lijn over werk, routes en dagelijkse situaties."
            ),
            open_loop="Pak de warme persoonlijke lijn op.",
            guardrails="Niet pushen zonder context.",
            risk_flags="",
            last_handoff_note=(
                "Gesprek niet resetten; de persoonlijke toon is al opgebouwd."
            ),
            last_approved_reply_style="Vertrouwd, plagerig en persoonlijk.",
        )
        ThreadFollowUpStatus.objects.create(
            thread=self.thread,
            status=ThreadFollowUpStatus.Status.WARM,
            note="Warme lijn vasthouden.",
            created_by=self.user,
            updated_by=self.user,
        )

    def assert_buddy_surface_present_and_safe(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buddy")
        self.assertContains(response, "Buddy status")
        self.assertContains(response, "Warm")
        self.assertContains(response, "Why now")
        self.assertContains(
            response,
            "Manually marked as warm",
        )
        self.assertContains(response, "Latest context")
        self.assertContains(response, "Active profile tone")
        self.assertContains(
            response,
            "Vertrouwd, plagerig en persoonlijk.",
        )
        self.assertContains(response, "Open loop")
        self.assertContains(
            response,
            "Pak de warme persoonlijke lijn op.",
        )
        self.assertContains(response, "Do not")
        self.assertContains(response, "Niet pushen zonder context.")
        self.assertContains(response, "Next step")
        self.assertContains(response, "Reliability")
        self.assertContains(response, "High")
        self.assertContains(
            response,
            "Core context, source and profile tone are available.",
        )

        html = response.content.decode()
        self.assertEqual(html.count('id="chat-buddy-context"'), 1)
        self.assertEqual(html.count("Buddy Context Surface"), 1)
        self.assertIn('data-chat-layout="messages-buddy"', html)
        self.assertLess(html.index("Messages"), html.index("Buddy Context Surface"))
        self.assertNotIn("Buddy-slot", html)
        self.assertNotIn("Intern reply draft voorstel", html)
        self.assertNotIn("Demo-context / menselijk checken", html)
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
        self.assertNotIn('"messages buddy"', html)
        self.assertNotIn('"followup buddy"', html)
        self.assertIn("chat-message-stream", html)
        self.assertIn("chat-follow-up-panel", html)
        self.assertLess(
            html.index("Messages"),
            html.index("Follow-up status"),
        )
        self.assertLess(
            html.index("Follow-up status"),
            html.index("Buddy Context Surface"),
        )
        self.assertIn("display: contents;", html)
        self.assertIn("order: 2;", html)
        self.assertIn("order: 3;", html)
        self.assertIn("@media (max-width: 1100px)", html)
        self.assertIn("@media (max-width: 720px)", html)
        self.assertIn("Context & safety", html)
        self.assertIn("Operational details", html)
        self.assertIn("Templates v1", html)
        self.assertIn("Session & handoff", html)
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

    def test_chats_normal_mode_shows_context_driven_buddy_surface(self):
        response = self.client.get(
            reverse("chat-hub"),
            {"thread": self.thread.pk},
        )

        self.assert_buddy_surface_present_and_safe(response)

    def test_chats_focus_mode_shows_context_driven_buddy_surface(self):
        response = self.client.get(
            reverse("chat-hub"),
            {"focus": "1", "thread": self.thread.pk},
        )

        self.assert_buddy_surface_present_and_safe(response)

    def test_buddy_surface_marks_risky_incomplete_context_as_low_reliability(self):
        self.thread.channel = None
        self.thread.thread_summary = ""
        self.thread.open_loop = ""
        self.thread.last_handoff_note = ""
        self.thread.last_approved_reply_style = ""
        self.thread.risk_flags = "Onbevestigde broncontext."
        self.thread.save(
            update_fields=[
                "channel",
                "thread_summary",
                "open_loop",
                "last_handoff_note",
                "last_approved_reply_style",
                "risk_flags",
                "updated_at",
            ]
        )

        response = self.client.get(
            reverse("chat-hub"),
            {"thread": self.thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Low")
        self.assertContains(response, "Risk signal present")
        self.assertContains(
            response,
            "Do not act until risk signals have been reviewed manually.",
        )
        self.assertContains(
            response,
            "Profile tone is missing; confirm it manually first.",
        )
