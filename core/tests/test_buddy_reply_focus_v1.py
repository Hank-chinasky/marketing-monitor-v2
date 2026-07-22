from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import (
    BuddyDraft,
    ConversationMessage,
    ConversationThread,
    Creator,
    CreatorChannel,
    Operator,
    OperatorAssignment,
)
from core.services.buddy_provider import PROVIDER_FACTORIES
from core.services.demo_access import (
    DEMO_DATA_MARKER,
    DEMO_VIEWER_GROUP_NAME,
)


class ConfiguredViewProvider:
    def generate_reply(
        self,
        *,
        context_packet,
    ):
        return {
            "draft_text": (
                "Ik ben vanavond nog even online. "
                "Wat maakte dat je vandaag weer aan me dacht?"
            ),
            "language": "nl",
            "why_this_reply": (
                "Het antwoord sluit aan op de persoonlijke open loop."
            ),
            "open_loops_to_watch": [
                "Vraag waarom hij vandaag aan het profiel dacht.",
            ],
            "do_not_do_warnings": [
                "Niet generiek openen.",
            ],
            "commercial_signal": "medium",
            "confidence": 0.84,
            "refusal_status": "none",
        }


class BuddyReplyFocusV1ViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.operator_user = user_model.objects.create_user(
            username="buddy-reply-operator",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)

        self.demo_user = user_model.objects.create_user(
            username="buddy-reply-demo",
            password="x",
            is_active=True,
        )
        demo_group = Group.objects.create(name=DEMO_VIEWER_GROUP_NAME)
        self.demo_user.groups.add(demo_group)

        self.creator = Creator.objects.create(
            display_name="[DEMO] Buddy Reply Creator",
            legal_name="",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
            notes=DEMO_DATA_MARKER,
        )

        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.OTHER,
            handle="buddy-reply-demo-source",
            profile_url="https://example.com/demo/buddy-reply",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.DRAFT_ONLY,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
        )

        self.thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_system=ConversationThread.SourceSystem.CHATTIES,
            source_thread_id="DEMO-BUDDY-REPLY-THREAD",
            source_site_id="SITE-42",
            source_site_label="Chatties demo",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            last_message_at=timezone.now(),
            thread_summary="Warme lopende democonversatie.",
            open_loop="Pak de bestaande persoonlijke lijn op.",
            guardrails="Niet generiek openen.",
            last_handoff_note="Behoud de vertrouwde toon.",
            last_approved_reply_style="Warm en persoonlijk.",
        )

        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=timezone.now(),
            active=True,
        )

        ConversationMessage.objects.create(
            thread=self.thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Demoklant",
            body="Ik moest vandaag weer aan je denken. Ben je vanavond nog online?",
            occurred_at=timezone.now(),
        )

        self.draft = BuddyDraft.objects.create(
            thread=self.thread,
            reply_text=(
                "Dat klinkt alsof ik precies op het juiste moment in je hoofd "
                "ben blijven hangen. Wat maakte dat je vandaag weer aan me dacht?"
            ),
            intent="warm_follow_up",
            tone="warm",
            risk_level=BuddyDraft.RiskLevel.LOW,
            state=BuddyDraft.State.DRAFTED,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

    @staticmethod
    def _opening_tag(html, element_id):
        marker = f'id="{element_id}"'
        start = html.index(marker)
        tag_start = html.rfind("<", 0, start)
        tag_end = html.index(">", start)
        return html[tag_start : tag_end + 1]

    def test_normal_operator_sees_editable_reply_focus(self):
        self.client.force_login(self.operator_user)

        response = self.client.get(
            reverse("chat-hub"),
            {"thread": self.thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Antwoord opstellen")
        self.assertContains(response, "Laatste klantbericht")
        self.assertContains(
            response,
            "Ik moest vandaag weer aan je denken.",
        )
        self.assertContains(response, self.draft.reply_text)
        self.assertContains(response, "Veilige tekst kopiëren")
        self.assertContains(response, "Verzendpreview maken")
        self.assertContains(response, "Bronhandoff")
        self.assertContains(response, "Chatties demo")
        self.assertContains(response, "SITE-42")
        self.assertContains(
            response,
            "DEMO-BUDDY-REPLY-THREAD",
        )
        self.assertNotContains(
            response,
            self.channel.profile_url,
        )
        self.assertContains(
            response,
            "Wijzigingen in dit vak worden niet opgeslagen.",
        )
        self.assertEqual(
            response.context["operator_reply_draft"]["status"],
            "existing_draft",
        )

        html = response.content.decode()
        textarea_tag = self._opening_tag(html, "buddy-reply-draft")
        send_button_tag = self._opening_tag(
            html,
            "buddy-reply-send-demo",
        )
        copy_button_tag = self._opening_tag(
            html,
            "buddy-reply-copy",
        )
        self.assertNotIn("readonly", textarea_tag)
        self.assertIn('type="button"', send_button_tag)
        self.assertNotIn("disabled", send_button_tag)
        self.assertNotIn('type="submit"', send_button_tag)
        self.assertIn("hidden", copy_button_tag)
        self.assertIn("disabled", copy_button_tag)
        self.assertNotIn(
            'id="buddy-open-source-profile"',
            html,
        )
        self.assertEqual(html.count("fetch("), 1)
        self.assertIn("new AbortController()", html)
        self.assertIn("signal: controller.signal", html)
        self.assertIn("textarea.value !== value", html)
        self.assertIn("error.name !== 'AbortError'", html)
        self.assertIn("let safePreviewText = '';", html)
        self.assertIn("copyButton.hidden = true", html)
        self.assertIn("copyButton.disabled = true", html)
        self.assertIn(
            "navigator.clipboard.writeText(",
            html,
        )
        self.assertIn("safePreviewText", html)
        self.assertIn(
            "document.createElement('textarea')",
            html,
        )
        self.assertNotIn(
            "navigator.clipboard.writeText(value)",
            html,
        )
        self.assertNotIn("Concept kopiëren", html)
        self.assertNotIn("Verzenden (demo)", html)
        self.assertIn(
            reverse("sanitized-send-preview"),
            html,
        )
        self.assertIn("Verzendpreview", html)
        self.assertIn(
            "Preview-only:",
            html,
        )
        self.assertNotIn("Buddy versturen", html)
        self.assertNotIn("Verstuur concept", html)

    def test_demo_viewer_sees_same_reply_focus_read_only(self):
        self.client.force_login(self.demo_user)

        response = self.client.get(
            reverse("chat-hub"),
            {"thread": self.thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["demo_read_only"])
        self.assertContains(response, "Antwoord opstellen")
        self.assertContains(response, self.draft.reply_text)
        self.assertContains(response, "Veilige tekst kopiëren")
        self.assertContains(response, "Verzendpreview maken")

        html = response.content.decode()
        textarea_tag = self._opening_tag(html, "buddy-reply-draft")
        copy_button_tag = self._opening_tag(html, "buddy-reply-copy")
        send_button_tag = self._opening_tag(
            html,
            "buddy-reply-send-demo",
        )

        self.assertIn("readonly", textarea_tag)
        self.assertIn('aria-readonly="true"', textarea_tag)
        self.assertIn("hidden", copy_button_tag)
        self.assertIn("disabled", copy_button_tag)
        self.assertIn("disabled", send_button_tag)
        self.assertNotIn(
            'id="buddy-open-source-profile"',
            html,
        )


    def test_operator_action_stays_below_messages_without_buddy_height_gap(self):
        self.client.force_login(self.operator_user)

        response = self.client.get(
            reverse("chat-hub"),
            {"thread": self.thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="chat-message-stream"')

        html = response.content.decode()
        message_index = html.index('class="chat-message-stream"')
        composer_index = html.index('data-operator-composer="v1"')
        action_index = html.index('data-operator-action="v1"')
        buddy_index = html.index('id="chat-buddy-context"')

        self.assertLess(message_index, composer_index)
        self.assertLess(composer_index, action_index)
        self.assertLess(action_index, buddy_index)
        self.assertEqual(
            html.count('data-operator-composer="v1"'),
            1,
        )
        self.assertNotIn('"followup buddy"', html)
        self.assertNotIn("grid-area: followup;", html)
        self.assertIn("display: contents;", html)
        self.assertIn(".chat-operator-composer {", html)
        self.assertIn("order: 4;", html)

    @override_settings(BUDDY_REPLY_PROVIDER="test-view")
    def test_configured_provider_runs_through_full_view_route(self):
        self.draft.delete()
        self.client.force_login(self.operator_user)

        with patch.dict(
            PROVIDER_FACTORIES,
            {
                "test-view": ConfiguredViewProvider,
            },
            clear=True,
        ):
            response = self.client.get(
                reverse("chat-hub"),
                {"thread": self.thread.pk},
            )

        self.assertEqual(response.status_code, 200)

        reply_draft = response.context["operator_reply_draft"]

        self.assertEqual(reply_draft["status"], "ready")
        self.assertEqual(
            reply_draft["reply_text"],
            (
                "Ik ben vanavond nog even online. "
                "Wat maakte dat je vandaag weer aan me dacht?"
            ),
        )
        self.assertEqual(reply_draft["language"], "nl")
        self.assertEqual(
            reply_draft["source"],
            "provider:ConfiguredViewProvider",
        )
        self.assertIn(
            "persoonlijke open loop",
            reply_draft["tone_note"],
        )
        self.assertTrue(reply_draft["requires_human_review"])

        self.assertContains(
            response,
            "Ik ben vanavond nog even online.",
        )
        self.assertNotContains(
            response,
            "Nog geen Buddy-antwoord",
        )

    def test_missing_provider_is_visible_and_not_a_fake_reply(self):
        self.draft.delete()
        self.client.force_login(self.operator_user)

        response = self.client.get(
            reverse("chat-hub"),
            {"thread": self.thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["operator_reply_draft"]["status"],
            "provider_unavailable",
        )
        self.assertEqual(
            response.context["operator_reply_draft"]["reply_text"],
            "",
        )
        self.assertContains(response, "Nog geen Buddy-antwoord")
        self.assertContains(
            response,
            "Buddy heeft in deze staat geen antwoord gegenereerd.",
        )
        self.assertNotContains(
            response,
            "Dankjewel voor je bericht. Ik kijk even goed",
        )
