from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
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
from core.services.demo_access import (
    DEMO_DATA_MARKER,
    DEMO_VIEWER_GROUP_NAME,
)


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
        self.assertContains(response, "Buddy conceptantwoord")
        self.assertContains(response, "Laatste klantbericht")
        self.assertContains(
            response,
            "Ik moest vandaag weer aan je denken.",
        )
        self.assertContains(response, self.draft.reply_text)
        self.assertContains(response, "Concept kopiëren")
        self.assertContains(
            response,
            "Geen automatische verzending of bron-writeback.",
        )
        self.assertEqual(
            response.context["operator_reply_draft"]["status"],
            "existing_draft",
        )

        html = response.content.decode()
        textarea_tag = self._opening_tag(html, "buddy-reply-draft")

        self.assertNotIn("readonly", textarea_tag)
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
        self.assertContains(response, "Buddy conceptantwoord")
        self.assertContains(response, self.draft.reply_text)
        self.assertContains(response, "Concept kopiëren")

        html = response.content.decode()
        textarea_tag = self._opening_tag(html, "buddy-reply-draft")
        copy_button_tag = self._opening_tag(html, "buddy-reply-copy")

        self.assertIn("readonly", textarea_tag)
        self.assertIn('aria-readonly="true"', textarea_tag)
        self.assertIn("disabled", copy_button_tag)

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
        self.assertContains(response, "Provider niet gekoppeld")
        self.assertContains(
            response,
            "Buddy heeft in deze staat geen antwoord gegenereerd.",
        )
        self.assertNotContains(
            response,
            "Dankjewel voor je bericht. Ik kijk even goed",
        )
