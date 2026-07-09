from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import (
    BuddyDraft,
    ConversationMessage,
    ConversationThread,
    Creator,
    CreatorChannel,
    CreatorMaterial,
    Operator,
    OperatorAssignment,
    ThreadFollowUpStatus,
)


class SharedCoreV1ViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="shared-core-user",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.user)

        self.admin_user = user_model.objects.create_user(
            username="shared-core-admin",
            password="x",
            is_active=True,
            is_staff=True,
        )

        self.creator = Creator.objects.create(
            display_name="Shared Core Creator",
            legal_name="Shared Core Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
            customer_stage=Creator.CustomerStage.INSIDE_PAYWALL,
            content_source_url="https://example.com/source",
            content_ready_status=Creator.ContentReadyStatus.READY_TO_POST,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="shared-core-channel",
            profile_url="https://example.com/shared-core-channel",
            access_notes="Use operator direct access only.",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
            session_next_action="Plan post for tomorrow morning.",
            session_blockers="-",
            session_updated_at=timezone.now() - timedelta(days=1),
        )
        self.newer_channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.TIKTOK,
            handle="recent-handoff-channel",
            profile_url="https://example.com/recent-handoff-channel",
            access_profile_notes="Use approved device profile.",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.AGENCY,
            credential_status=CreatorChannel.CredentialStatus.KNOWN,
            two_factor_enabled=True,
            session_next_action="Escalate risky comments to Chats.",
            session_blockers="Awaiting creator approval.",
            session_updated_at=timezone.now(),
        )

        self.assignment = OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator,
            scope=OperatorAssignment.Scope.FULL_MANAGEMENT,
            starts_at=timezone.now() - timedelta(days=1),
            active=True,
        )

        self.thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.channel,
            source_thread_id="shared-core-thread",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            open_loop="Reply with updated delivery date.",
            guardrails="No promises without confirmed date.",
            risk_flags="",
            last_handoff_note="Need manual approval before final reply.",
        )
        self.handoff_thread = ConversationThread.objects.create(
            creator=self.creator,
            channel=self.newer_channel,
            source_thread_id="priority-handoff-thread",
            status=ConversationThread.Status.HANDOFF_REQUIRED,
            open_loop="Escalate to chat operator now.",
            guardrails="Keep message concise.",
            risk_flags="",
            last_handoff_note="Ready for urgent handoff.",
        )
        BuddyDraft.objects.create(
            thread=self.thread,
            reply_text="Dankjewel! We komen morgen met update.",
            intent="follow_up",
            tone="warm",
            risk_level=BuddyDraft.RiskLevel.LOW,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

        self.other_creator = Creator.objects.create(
            display_name="Out Scope Creator",
            legal_name="Out Scope Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.other_thread = ConversationThread.objects.create(
            creator=self.other_creator,
            source_thread_id="out-scope-thread",
            status=ConversationThread.Status.WAITING_ON_OPERATOR,
            open_loop="Out of scope action",
            guardrails="Out scope guardrail",
        )

        CreatorMaterial.objects.create(
            creator=self.creator,
            uploaded_by=self.user,
            file="creator_materials/demo.txt",
            label="Feeder item",
            active=True,
        )

    def test_creator_customer_stage_defaults_to_unknown_and_choices_are_stable(self):
        creator = Creator.objects.create(
            display_name="Default Stage Creator",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )

        self.assertEqual(creator.customer_stage, Creator.CustomerStage.UNKNOWN)
        self.assertEqual(creator.get_customer_stage_display(), "Unknown")
        self.assertEqual(
            [value for value, _label in Creator.CustomerStage.choices],
            [
                "unknown",
                "lead",
                "outside_paywall",
                "inside_paywall",
                "former_customer",
                "blocked_do_not_contact",
            ],
        )

    def test_creator_detail_shows_customer_stage_read_only(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer stage")
        self.assertContains(response, "Inside paywall")

    def test_chat_and_feeder_keep_fixed_pane_roles(self):
        self.client.force_login(self.user)
        chats = self.client.get(reverse("chat-hub"))
        feeder = self.client.get(reverse("feeder-hub"))

        self.assertContains(chats, "Policy · Context · Scope · Access/Risk · Completeness")
        self.assertContains(chats, "Werkvlak: threadfocus en actuele aandacht")
        self.assertContains(chats, "Handoff · Run log · Open issues · Quick actions · Buddy-slot")

        self.assertContains(feeder, "Policy · Context · Scope · Access/Risk · Completeness")
        self.assertContains(feeder, "Werkvlak: creatorselectie, feedfocus en opvolging")
        self.assertContains(feeder, "Handoff · Run log · Signals · Quick actions · Buddy-slot")

    def test_chats_still_shows_access_and_completeness_modules(self):
        self.client.force_login(self.user)
        chats = self.client.get(reverse("chat-hub"))

        self.assertContains(chats, "Mag ik hier werken?")
        self.assertContains(chats, "Assignment status")
        self.assertContains(chats, "Completeness alerts")

    def test_chats_requires_login_for_anonymous_user(self):
        response = self.client.get(reverse("chat-hub"))
        focus_response = self.client.get(reverse("chat-hub"), {"focus": "1"})

        self.assertIn(response.status_code, [302, 401, 403])
        if response.status_code == 302:
            self.assertIn("/login/", response["Location"])

        self.assertIn(focus_response.status_code, [302, 401, 403])
        if focus_response.status_code == 302:
            self.assertIn("/login/", focus_response["Location"])

    def test_chats_normal_mode_still_renders_without_focus_banner(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chats Workspace v1")
        self.assertContains(response, "AdultAdSuite / CreatorWorkboardFlow")
        self.assertContains(response, "AdultAdSuite dagstart")
        self.assertContains(response, "/adultadsuite/")
        self.assertContains(response, "/chats/?focus=1")
        self.assertContains(response, "Actief: normale werkvloer")
        self.assertContains(response, "Klantenstatus / Follow-up")
        self.assertContains(response, "Gebruik deze lijst om bewust te kiezen")
        self.assertContains(response, "warm")
        self.assertContains(response, "open loop")
        self.assertContains(response, "Later triggeren")
        self.assertContains(response, "Afgekoeld")
        self.assertContains(response, "Review nodig")
        self.assertContains(response, "Statuskeuze")
        self.assertContains(response, "Optionele operatornotitie")
        self.assertContains(response, "Opslaan follow-up status")
        self.assertContains(response, "Nog geen follow-up status vastgelegd")
        self.assertContains(response, "De operator kiest handmatig")
        self.assertNotContains(response, "CreatorWorkboardFlow Focusstand")
        self.assertNotContains(response, "Buddy Context")
        self.assertFalse(response.context["focus_mode"])

    def test_chats_focus_mode_renders_focus_banner_and_backlink(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("chat-hub"),
            {"focus": "1", "thread": self.thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CreatorWorkboardFlow Focusstand")
        self.assertContains(response, "AdultAdSuite / CreatorWorkboardFlow")
        self.assertContains(response, "AdultAdSuite dagstart")
        self.assertContains(response, "/adultadsuite/")
        self.assertContains(response, "Normale stand")
        self.assertContains(response, "Actief: focusstand")
        self.assertContains(response, "Minder afleiding. Werk één gesprek of opvolgstap bewust af.")
        self.assertContains(response, "Terug naar normale stand")
        self.assertContains(response, "/chats/")
        self.assertContains(response, "Buddy Context")
        self.assertContains(response, "Follow-up status")
        self.assertContains(response, "Check eerst of dit gesprek warm, open loop, later triggeren, afgekoeld of review nodig is.")
        self.assertContains(response, "Geen automatische ranking, trigger of verzending")
        self.assertContains(response, "Statuskeuze")
        self.assertContains(response, "Optionele korte operatornotitie")
        self.assertContains(response, "Opslaan follow-up status")
        self.assertContains(response, "Warm")
        self.assertContains(response, "Open loop")
        self.assertContains(response, "Waar moet ik op letten?")
        self.assertContains(response, "Laatste context")
        self.assertContains(response, "Gesprek/contextstatus")
        self.assertContains(response, "Operator focus")
        self.assertContains(response, "Follow-up hint")
        self.assertContains(response, "Revenue moment")
        self.assertContains(response, "Safety boundary")
        self.assertContains(response, "Buddy adviseert")
        self.assertContains(response, "De operator beslist")
        self.assertContains(response, "Geen automatische verzending")
        self.assertTrue(response.context["focus_mode"])

    def test_chats_focus_mode_buddy_context_has_safe_empty_state_without_thread(self):
        ConversationThread.objects.filter(creator=self.creator).delete()

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"focus": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CreatorWorkboardFlow Focusstand")
        self.assertContains(response, "Buddy Context")
        self.assertContains(response, "Nog geen specifiek gesprek geselecteerd")
        self.assertContains(response, "Open of kies een gesprek om Buddy-context te gebruiken")
        self.assertContains(response, "Safety boundary")
        self.assertContains(response, "Buddy adviseert")
        self.assertContains(response, "De operator beslist")
        self.assertContains(response, "Nog geen gesprek geselecteerd. Kies een gesprek om follow-up status vast te leggen.")
        self.assertTrue(response.context["focus_mode"])
        self.assertIsNone(response.context["selected_thread"])

    def test_chats_manual_follow_up_empty_state_without_thread(self):
        ConversationThread.objects.filter(creator=self.creator).delete()

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Klantenstatus / Follow-up")
        self.assertContains(response, "Kies eerst een gesprek om follow-up status vast te leggen.")
        self.assertIsNone(response.context["selected_thread"])

    def test_chats_manual_follow_up_status_saves_warm_with_note(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "thread": self.thread.pk,
                "follow_up_status": ThreadFollowUpStatus.Status.WARM,
                "follow_up_note": "Vandaag warm opvolgen met rustige opening.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"thread={self.thread.pk}", response["Location"])
        self.assertIn("follow_up_saved=1", response["Location"])

        follow_up_status = ThreadFollowUpStatus.objects.get(thread=self.thread)
        self.assertEqual(follow_up_status.status, ThreadFollowUpStatus.Status.WARM)
        self.assertEqual(
            follow_up_status.note,
            "Vandaag warm opvolgen met rustige opening.",
        )
        self.assertEqual(follow_up_status.created_by, self.user)
        self.assertEqual(follow_up_status.updated_by, self.user)

        saved_response = self.client.get(response["Location"])
        self.assertContains(saved_response, "Follow-up status opgeslagen")
        self.assertContains(saved_response, "Laatst opgeslagen")
        self.assertContains(saved_response, "Warm")
        self.assertContains(saved_response, "Vandaag warm opvolgen met rustige opening.")

    def test_chats_manual_follow_up_status_saves_open_loop_and_preserves_focus(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "form_action": "follow_up_status",
                "focus": "1",
                "thread": self.thread.pk,
                "follow_up_status": ThreadFollowUpStatus.Status.OPEN_LOOP,
                "follow_up_note": "Klant vroeg om later terug te komen.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("focus=1", response["Location"])
        self.assertIn(f"thread={self.thread.pk}", response["Location"])
        self.assertIn("follow_up_saved=1", response["Location"])

        follow_up_status = ThreadFollowUpStatus.objects.get(thread=self.thread)
        self.assertEqual(
            follow_up_status.status,
            ThreadFollowUpStatus.Status.OPEN_LOOP,
        )
        self.assertEqual(follow_up_status.note, "Klant vroeg om later terug te komen.")

        saved_response = self.client.get(response["Location"])
        self.assertContains(saved_response, "CreatorWorkboardFlow Focusstand")
        self.assertContains(saved_response, "Buddy Context")
        self.assertContains(saved_response, "Follow-up status opgeslagen")
        self.assertContains(saved_response, "Open loop")
        self.assertContains(saved_response, "Klant vroeg om later terug te komen.")
        self.assertContains(saved_response, "Buddy adviseert")
        self.assertContains(saved_response, "De operator beslist")
        self.assertContains(saved_response, "Geen automatische ranking, trigger of verzending")

    def test_chats_shows_customer_stage_read_only_context(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer stage")
        self.assertContains(response, "Inside paywall")

    def test_feeder_shows_customer_stage_read_only_context(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"), {"creator": self.creator.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer stage")
        self.assertContains(response, "Inside paywall")

    def test_chats_message_panel_renders_selected_thread_messages_read_only(self):
        older_message = ConversationMessage.objects.create(
            thread=self.thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Customer",
            body="Eerste bericht van klant.",
            occurred_at=timezone.now() - timedelta(minutes=2),
        )
        newer_message = ConversationMessage.objects.create(
            thread=self.thread,
            direction=ConversationMessage.Direction.OUTBOUND,
            sender_label="Operator",
            body="Antwoord van operator.",
            occurred_at=timezone.now() - timedelta(minutes=1),
        )
        ConversationMessage.objects.create(
            thread=self.handoff_thread,
            direction=ConversationMessage.Direction.INTERNAL_NOTE,
            sender_label="Internal",
            body="Bericht op andere selected_thread mag niet lekken.",
            occurred_at=timezone.now(),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Berichten")
        self.assertContains(response, "Read-only berichtenstroom uit de geselecteerde thread.")
        self.assertContains(response, "Klant")
        self.assertContains(response, "Customer")
        self.assertContains(response, "Eerste bericht van klant.")
        self.assertContains(response, "Operator")
        self.assertContains(response, "Antwoord van operator.")
        self.assertNotContains(response, "Bericht op andere selected_thread mag niet lekken.")
        self.assertEqual(
            list(response.context["conversation_messages"]),
            [older_message, newer_message],
        )
        html = response.content.decode()
        self.assertLess(
            html.index("Eerste bericht van klant."),
            html.index("Antwoord van operator."),
        )
        self.assertNotContains(response, "Bericht toevoegen")
        self.assertNotContains(response, 'name="message_body"')
        self.assertNotContains(response, "Importeer berichten")

    def test_chats_focus_mode_message_stream_renders_selected_thread_messages_read_only(self):
        ConversationMessage.objects.create(
            thread=self.thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Customer",
            body="Focus klantbericht.",
            occurred_at=timezone.now() - timedelta(minutes=2),
        )
        ConversationMessage.objects.create(
            thread=self.thread,
            direction=ConversationMessage.Direction.OUTBOUND,
            sender_label="Operator",
            body="Focus operatorbericht.",
            occurred_at=timezone.now() - timedelta(minutes=1),
        )

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("chat-hub"),
            {"focus": "1", "thread": self.thread.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CreatorWorkboardFlow Focusstand")
        self.assertContains(response, "Berichten")
        self.assertContains(response, "Klant")
        self.assertContains(response, "Focus klantbericht.")
        self.assertContains(response, "Operator")
        self.assertContains(response, "Focus operatorbericht.")
        self.assertNotContains(response, "Importeer berichten")

    def test_chats_message_panel_shows_empty_state_without_messages(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Berichten")
        self.assertContains(response, "Nog geen berichten opgeslagen voor dit gesprek.")
        self.assertEqual(list(response.context["conversation_messages"]), [])

    def test_chats_message_panel_fallback_without_thread_is_empty(self):
        ConversationThread.objects.filter(creator=self.creator).delete()
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["conversation_messages"], [])
        self.assertContains(response, "Berichten")
        self.assertContains(response, "Kies een gesprek om berichten te bekijken.")
        self.assertContains(response, "Selecteer een thread om het werkvlak te starten.")

    def test_feeder_keeps_operator_first_five_center_blocks(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertContains(response, "Wat live moet")
        self.assertContains(response, "Wat aandacht nodig heeft")
        self.assertContains(response, "Content/context vóór actie")
        self.assertContains(response, "Door naar Chats")
        self.assertContains(response, "Ritme / opvolging")

    def test_feeder_pre_action_context_block_renders_scanable_items(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Content/context vóór actie")
        self.assertContains(response, "Content status")
        self.assertContains(response, "Content source")
        self.assertContains(response, "Laatste materiaal")
        self.assertContains(response, "Kanaalfocus")
        self.assertContains(response, "https://example.com/source")
        self.assertContains(response, "Feeder item")
        self.assertContains(response, "recent-handoff-channel")

    def test_feeder_scan_context_is_present_in_template_and_context(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"), {"creator": self.creator.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Feeder scan")
        self.assertContains(response, "Live focus")
        self.assertContains(response, "Laatste feeder-handoff")
        self.assertContains(response, "Volgende operatoractie")
        self.assertContains(response, "Chats-handoff scan")
        self.assertIn("feeder_focus_items", response.context)
        self.assertIn("latest_feeder_handoff_scan", response.context)
        self.assertIn("next_operator_action_scan", response.context)
        self.assertIn("chats_handoff_scan", response.context)
        self.assertEqual(
            response.context["latest_feeder_handoff_scan"]["channel"],
            "TikTok / recent-handoff-channel",
        )
        self.assertEqual(
            response.context["next_operator_action_scan"],
            "Escalate risky comments to Chats.",
        )
        self.assertEqual(response.context["chats_handoff_scan"]["count"], 2)

    def test_feeder_scan_next_operator_action_uses_actionable_completeness_fallback(self):
        self.creator.content_source_url = ""
        self.creator.save(update_fields=["content_source_url"])

        self.channel.session_next_action = ""
        self.channel.save(update_fields=["session_next_action"])
        self.newer_channel.session_next_action = ""
        self.newer_channel.save(update_fields=["session_next_action"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"), {"creator": self.creator.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["next_operator_action_scan"],
            "Los eerst op: Content source URL ontbreekt.",
        )
        self.assertContains(response, "Los eerst op: Content source URL ontbreekt.")

    def test_feeder_pre_action_context_handles_missing_material_and_channels(self):
        CreatorMaterial.objects.filter(creator=self.creator).delete()
        CreatorChannel.objects.filter(creator=self.creator).delete()

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"), {"creator": self.creator.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Content/context vóór actie")
        self.assertContains(response, "Geen actief materiaal beschikbaar.")
        self.assertContains(response, "Geen kanaal in scope.")

    def test_feeder_chats_quick_action_prioritizes_handoff_required(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertContains(response, f"/chats/?thread={self.handoff_thread.pk}")
        self.assertEqual(
            response.context["follow_up_summary"]["next_chats_thread_id"],
            self.handoff_thread.pk,
        )

    def test_feeder_placeholder_noise_filter_ignores_blocker_placeholders(self):
        self.channel.session_blockers = "n/a"
        self.channel.save(update_fields=["session_blockers"])
        self.newer_channel.session_blockers = "-"
        self.newer_channel.save(update_fields=["session_blockers"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertNotContains(response, "blocker: n/a")
        self.assertNotContains(response, "blocker: -")

    def test_feeder_ritme_opvolging_shows_status_step_and_work_target(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertContains(response, "Laatste stand:")
        self.assertContains(response, "Volgende stap:")
        self.assertContains(response, "Vervolgwerk zit in:")

    def test_feeder_buddy_slot_is_visible_and_renders_without_crash(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buddy-slot")
        self.assertContains(response, "Korte creator-samenvatting")
        self.assertContains(response, "Ontbrekende velden/contextgaten")
        self.assertContains(response, "Voorgestelde volgende stap")
        self.assertContains(response, "Compacte sessiebrief")
        self.assertContains(response, "Wat live moet")
        self.assertContains(response, "Wat aandacht nodig heeft")
        self.assertContains(response, "Content/context vóór actie")
        self.assertContains(response, "Door naar Chats")
        self.assertContains(response, "Ritme / opvolging")

    def test_feeder_buddy_slot_shows_context_prefill_for_selected_creator(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"), {"creator": self.creator.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Context prefill")
        self.assertContains(response, "Shared Core Creator")
        self.assertContains(response, "Inside paywall")
        self.assertContains(response, "Ready to post")
        self.assertContains(response, "https://example.com/source")
        self.assertContains(response, "TikTok / recent-handoff-channel")
        self.assertContains(response, "https://example.com/recent-handoff-channel")
        self.assertContains(response, "Use approved device profile.")
        self.assertIn(
            {"label": "Customer stage", "value": "Inside paywall"},
            response.context["buddy_assist"]["context_prefill"],
        )
        self.assertIn(
            {"label": "Content status", "value": "Ready to post"},
            response.context["buddy_assist"]["context_prefill"],
        )
        self.assertIn(
            {"label": "Channel", "value": "TikTok / recent-handoff-channel"},
            response.context["buddy_assist"]["context_prefill"],
        )

    def test_feeder_buddy_slot_handles_missing_context(self):
        self.creator.content_source_url = ""
        self.creator.content_ready_status = ""
        self.creator.save(update_fields=["content_source_url", "content_ready_status"])
        self.channel.session_next_action = ""
        self.channel.session_blockers = ""
        self.channel.save(update_fields=["session_next_action", "session_blockers"])
        self.newer_channel.session_next_action = ""
        self.newer_channel.session_blockers = "-"
        self.newer_channel.save(update_fields=["session_next_action", "session_blockers"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Content source URL ontbreekt.")
        self.assertContains(response, "Content ready status ontbreekt.")
        self.assertContains(response, "Volgende stap ontbreekt in channel sessiecontext.")
        self.assertContains(response, "Gecondenseerde laatste handoff:")
        self.assertContains(response, "Niet beschikbaar.")

    def test_feeder_buddy_slot_shows_condensed_handoff_when_available(self):
        self.newer_channel.session_blockers = (
            "Creator wacht op korte planning en bevestiging van publicatiemoment."
        )
        self.newer_channel.session_next_action = "Plan conceptpost en bevestig timing."
        self.newer_channel.save(update_fields=["session_blockers", "session_next_action"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shared Core Creator · Ready to post")
        self.assertContains(response, "Plan conceptpost en bevestig timing.")
        self.assertContains(response, "Gecondenseerde laatste handoff")
        self.assertContains(
            response,
            "Creator wacht op korte planning en bevestiging van publicatiemoment.",
        )

    def test_feeder_buddy_slot_uses_next_step_as_handoff_fallback(self):
        self.newer_channel.session_blockers = ""
        self.newer_channel.session_next_action = "Werk caption uit en plan uploadmoment."
        self.newer_channel.save(update_fields=["session_blockers", "session_next_action"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gecondenseerde laatste handoff")
        self.assertContains(response, "Werk caption uit en plan uploadmoment.")
        self.assertNotContains(response, "Niet beschikbaar.")

    def test_feeder_buddy_slot_get_is_read_only_without_side_effects_or_chats_strings(self):
        before_status = self.creator.content_ready_status
        before_next_step = self.newer_channel.session_next_action
        before_blockers = self.newer_channel.session_blockers
        before_material_count = CreatorMaterial.objects.count()

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertEqual(response.status_code, 200)
        self.creator.refresh_from_db()
        self.newer_channel.refresh_from_db()
        self.assertEqual(self.creator.content_ready_status, before_status)
        self.assertEqual(self.newer_channel.session_next_action, before_next_step)
        self.assertEqual(self.newer_channel.session_blockers, before_blockers)
        self.assertEqual(CreatorMaterial.objects.count(), before_material_count)
        self.assertNotContains(response, "Korte threadsamenvatting")
        self.assertNotContains(response, "Open thread detail")

    def test_templates_are_reachable_from_chats_and_feeder(self):
        self.client.force_login(self.user)
        chats = self.client.get(reverse("chat-hub"))
        feeder = self.client.get(reverse("feeder-hub"))

        self.assertContains(chats, "Templates v1")
        self.assertContains(chats, "Handoff follow-up update")
        self.assertContains(feeder, "Templates v1")
        self.assertContains(feeder, "Feeder content readiness check")

    def test_template_list_search_supports_title_type_and_tag_in_chats(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("chat-hub"),
            {
                "thread": self.thread.pk,
                "template_q": "handoff",
                "template_type": "handoff",
                "template_tag": "operator",
            },
        )

        self.assertContains(response, "Handoff follow-up update")
        self.assertNotContains(response, "Risk review ping")

    def test_template_open_and_duplicate_fill_in_chats(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("chat-hub"),
            {
                "thread": self.thread.pk,
                "template": "handoff_followup",
            },
        )

        self.assertContains(response, "Template geopend:")
        self.assertContains(response, "Handoff follow-up update")
        self.assertContains(response, "Korte update via Instagram (shared-core-channel).")
        self.assertContains(response, "Volgende stap: Reply with updated delivery date..")

    def test_template_usage_is_visible_in_chat_run_log_context(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("chat-hub"),
            {
                "thread": self.thread.pk,
                "template": "handoff_followup",
                "template_action": "use",
            },
        )

        self.assertContains(response, "Template geopend")
        self.assertContains(response, "Template gebruikt")

    def test_template_open_fill_and_run_log_visibility_in_feeder(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("feeder-hub"),
            {
                "creator": self.creator.pk,
                "template": "feeder_content_ready",
                "template_action": "use",
            },
        )

        self.assertContains(response, "Template geopend:")
        self.assertContains(response, "Feeder content readiness check")
        self.assertContains(response, "Status: Ready to post")
        self.assertContains(response, "Template gebruikt")

    def test_feeder_template_fill_ignores_placeholder_noise_values(self):
        self.newer_channel.session_next_action = "n/a"
        self.newer_channel.session_blockers = "-"
        self.newer_channel.save(update_fields=["session_next_action", "session_blockers"])
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("feeder-hub"),
            {
                "creator": self.creator.pk,
                "template": "feeder_content_ready",
            },
        )

        self.assertNotContains(response, "Laatste handoff: -")
        self.assertNotContains(response, "Volgende stap: n/a")

    def test_chat_buddy_slot_renders_assist_sections(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertContains(response, "Buddy-slot")
        self.assertContains(response, "Korte threadsamenvatting")
        self.assertContains(response, "Ontbrekende velden")
        self.assertContains(response, "Voorgestelde volgende stap")
        self.assertContains(response, "Compacte sessiebrief")
        self.assertContains(response, "Shared Core Creator")
        self.assertContains(response, "Reply with updated delivery date.")

    def test_chat_buddy_slot_shows_operator_reply_draft_read_only_from_service(self):
        BuddyDraft.objects.filter(thread=self.thread).delete()
        ConversationMessage.objects.create(
            thread=self.thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Customer",
            body="Hello, can you help me with the delivery date?",
            occurred_at=timezone.now(),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Intern reply draft voorstel")
        self.assertContains(response, "Thanks for your message")
        self.assertContains(response, "deterministic_quality_v1")
        self.assertContains(response, "Human review:")
        self.assertContains(response, "Read-only operatorconcept")
        self.assertEqual(response.context["operator_reply_draft"]["language"], "en")
        self.assertEqual(
            response.context["operator_reply_draft"]["source"],
            "deterministic_quality_v1",
        )
        self.assertTrue(response.context["operator_reply_draft"]["requires_human_review"])
        self.assertNotContains(response, "Bericht versturen")
        self.assertNotContains(response, 'name="reply_text"')
        self.assertNotContains(response, 'name="message_body"')

    def test_chat_buddy_slot_uses_latest_buddy_draft_through_service_boundary(self):
        ConversationMessage.objects.create(
            thread=self.thread,
            direction=ConversationMessage.Direction.INBOUND,
            sender_label="Klant",
            body="Hoi, kun je mij morgen helpen?",
            occurred_at=timezone.now(),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dankjewel! We komen morgen met update.")
        self.assertEqual(response.context["operator_reply_draft"]["language"], "nl")
        self.assertEqual(
            response.context["operator_reply_draft"]["source"],
            "latest_buddy_draft",
        )
        self.assertNotContains(response, "Bericht versturen")
        self.assertNotContains(response, 'name="reply_text"')

    def test_chat_hub_shows_manual_thread_intake_entrypoint_for_scoped_operator(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_create_conversation_thread"])
        self.assertContains(response, "Nieuwe conversation thread")
        self.assertContains(
            response,
            "Maak handmatig een thread aan voor een livechat, DM of bestaande klant.",
        )
        self.assertContains(response, reverse("conversation-thread-create"))

    def test_chat_hub_hides_manual_thread_intake_entrypoint_for_unsupported_user(self):
        user_model = get_user_model()
        unsupported_user = user_model.objects.create_user(
            username="unsupported-chat-entrypoint",
            password="x",
            is_active=True,
        )
        self.client.force_login(unsupported_user)
        response = self.client.get(reverse("chat-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_create_conversation_thread"])
        self.assertNotContains(response, "Nieuwe conversation thread")
        self.assertNotContains(response, "livechat, DM of bestaande klant")

    def test_chat_buddy_slot_shows_context_prefill_for_selected_thread(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Context prefill")
        self.assertContains(response, "Creator")
        self.assertContains(response, "Shared Core Creator")
        self.assertContains(response, "Inside paywall")
        self.assertContains(response, "Instagram / shared-core-channel")
        self.assertContains(response, "https://example.com/shared-core-channel")
        self.assertContains(response, "Use operator direct access only.")
        self.assertContains(response, "Guardrails")
        self.assertContains(response, "No promises without confirmed date.")
        self.assertNotContains(response, "Out Scope Creator")
        self.assertIn(
            {"label": "Creator", "value": "Shared Core Creator"},
            response.context["buddy_assist"]["context_prefill"],
        )
        self.assertIn(
            {"label": "Customer stage", "value": "Inside paywall"},
            response.context["buddy_assist"]["context_prefill"],
        )
        self.assertIn(
            {"label": "Channel", "value": "Instagram / shared-core-channel"},
            response.context["buddy_assist"]["context_prefill"],
        )
        self.assertIn(
            {"label": "Guardrails", "value": "No promises without confirmed date."},
            response.context["buddy_assist"]["context_prefill"],
        )

    def test_chat_buddy_assist_signals_missing_context_when_thread_is_incomplete(self):
        self.thread.guardrails = ""
        self.thread.open_loop = ""
        self.thread.last_handoff_note = ""
        self.thread.save(update_fields=["guardrails", "open_loop", "last_handoff_note"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertContains(response, "Guardrails ontbreken; policy-context is onvolledig.")
        self.assertContains(response, "Volgende stap ontbreekt (open loop leeg).")
        self.assertContains(response, "Laatste handoff-status ontbreekt.")
        self.assertContains(response, "Los eerst op: Volgende stap ontbreekt (open loop leeg).")
        self.assertEqual(
            response.context["next_step_scan"],
            "Los eerst op: Volgende stap ontbreekt (open loop leeg).",
        )

    def test_assignment_scope_status_is_rendered_in_chats_and_feeder(self):
        self.client.force_login(self.user)

        chats_response = self.client.get(reverse("chat-hub"))
        feeder_response = self.client.get(reverse("feeder-hub"))

        self.assertContains(chats_response, "actieve assignment")
        self.assertContains(chats_response, self.assignment.get_scope_display())

        self.assertContains(feeder_response, "actieve assignment")
        self.assertContains(feeder_response, self.assignment.get_scope_display())

    def test_chats_access_state_blocked_without_operator_assignment(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("chat-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "blocked")
        self.assertContains(response, "Geen actieve operator-assignment voor deze creator.")

    def test_feeder_access_state_blocked_without_operator_assignment(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "blocked")
        self.assertContains(response, "Geen actieve operator-assignment voor deze creator.")

    def test_chats_access_state_blocked_when_assignment_scope_disallows_chat(self):
        self.assignment.scope = OperatorAssignment.Scope.POSTING_ONLY
        self.assignment.save(update_fields=["scope"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"))

        self.assertContains(response, "blocked")
        self.assertContains(response, "Assignment-scope laat geen chat-operatoractie toe.")

    def test_chat_access_is_review_needed_when_open_loop_missing(self):
        self.thread.open_loop = ""
        self.thread.save(update_fields=["open_loop"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertContains(response, "review_needed")
        self.assertContains(response, "Volgende stap ontbreekt (open loop leeg).")

    def test_chat_access_is_review_needed_when_handoff_missing(self):
        self.thread.last_handoff_note = ""
        self.thread.save(update_fields=["last_handoff_note"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertContains(response, "review_needed")
        self.assertContains(response, "Laatste handoff-status ontbreekt.")

    def test_chat_completeness_alerts_visible_when_context_missing(self):
        self.thread.guardrails = ""
        self.thread.open_loop = ""
        self.thread.last_handoff_note = ""
        self.thread.save(update_fields=["guardrails", "open_loop", "last_handoff_note"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertContains(response, "Guardrails ontbreken; policy-context is onvolledig.")
        self.assertContains(response, "Volgende stap ontbreekt (open loop leeg).")
        self.assertContains(response, "Laatste handoff-status ontbreekt.")

    def test_feeder_completeness_alerts_visible_when_context_missing(self):
        self.creator.content_source_url = ""
        self.creator.content_ready_status = ""
        self.creator.save(update_fields=["content_source_url", "content_ready_status"])

        self.channel.session_next_action = ""
        self.channel.save(update_fields=["session_next_action"])
        self.newer_channel.session_next_action = ""
        self.newer_channel.save(update_fields=["session_next_action"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertContains(response, "Content source URL ontbreekt.")
        self.assertContains(response, "Content ready status ontbreekt.")
        self.assertContains(response, "Volgende stap ontbreekt in channel sessiecontext.")

    def test_feeder_completeness_treats_placeholder_next_steps_as_missing(self):
        self.channel.session_next_action = "-"
        self.channel.save(update_fields=["session_next_action"])
        self.newer_channel.session_next_action = "n/a"
        self.newer_channel.save(update_fields=["session_next_action"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertContains(response, "Volgende stap ontbreekt in channel sessiecontext.")

    def test_feeder_handoff_runlog_and_channel_quick_action_use_same_relevant_channel(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "recent-handoff-channel")
        self.assertContains(response, f"/channels/{self.newer_channel.pk}/")

        self.assertEqual(response.context["relevant_handoff_channel"].pk, self.newer_channel.pk)
        self.assertEqual(response.context["run_log"][0]["value"], self.newer_channel.session_updated_at)

    def test_chat_hub_shows_operator_flow_modules(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"))

        self.assertContains(response, "Sessie starten")
        self.assertContains(response, "Sessie afsluiten")
        self.assertContains(response, "Top chat focus")
        self.assertContains(response, "Volgende stap (scanbaar)")

    def test_next_step_prefills_from_current_open_loop(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertContains(response, 'name="next_step" value="Reply with updated delivery date."')

    def test_handoff_form_keeps_values_on_validation_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "thread": str(self.thread.pk),
                "handoff_summary": "",
                "next_step": "Volgende stap blijft staan",
                "blocker": "Nog blocker",
                "close_signal": "review_nodig",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laatste stand en volgende stap zijn verplicht om af te sluiten.")
        self.assertContains(response, 'name="next_step" value="Volgende stap blijft staan"')
        self.assertContains(response, 'name="blocker" value="Nog blocker"')
        self.assertContains(response, 'option value="review_nodig" selected')

    def test_get_fallback_still_selects_first_thread(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{reverse('chat-hub')}?thread=invalid")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "shared-core-thread")

    def test_post_without_thread_id_writes_nothing(self):
        self.client.force_login(self.user)
        old_note = self.thread.last_handoff_note
        response = self.client.post(
            reverse("chat-hub"),
            {
                "handoff_summary": "Test zonder thread",
                "next_step": "Volgende stap",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.last_handoff_note, old_note)
        self.assertContains(response, "Geen actieve thread geselecteerd voor handoff-afsluiting.")

    def test_post_with_invalid_thread_id_writes_nothing(self):
        self.client.force_login(self.user)
        old_note = self.thread.last_handoff_note
        response = self.client.post(
            reverse("chat-hub"),
            {
                "thread": "abc",
                "handoff_summary": "Test ongeldige thread",
                "next_step": "Volgende stap",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.last_handoff_note, old_note)
        self.assertContains(response, "Geen actieve thread geselecteerd voor handoff-afsluiting.")

    def test_post_with_out_of_scope_thread_writes_nothing(self):
        self.client.force_login(self.user)
        old_note = self.thread.last_handoff_note
        response = self.client.post(
            reverse("chat-hub"),
            {
                "thread": str(self.other_thread.pk),
                "handoff_summary": "Test out of scope",
                "next_step": "Volgende stap",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.thread.refresh_from_db()
        self.other_thread.refresh_from_db()
        self.assertEqual(self.thread.last_handoff_note, old_note)
        self.assertNotIn("Test out of scope", self.other_thread.last_handoff_note)
        self.assertContains(response, "Geen actieve thread geselecteerd voor handoff-afsluiting.")

    def test_operator_can_submit_handoff_and_update_thread_fields(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("chat-hub"),
            {
                "thread": str(self.thread.pk),
                "handoff_summary": "Gesprek afgerond en klant geïnformeerd.",
                "next_step": "Morgen opvolgen of klant heeft gereageerd.",
                "blocker": "Wacht op klantreactie.",
                "close_signal": "opvolging_nodig",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.redirect_chain)
        self.assertIn("/chats/?thread=", response.redirect_chain[0][0])
        self.assertIn("saved=1", response.redirect_chain[0][0])
        self.thread.refresh_from_db()
        self.assertIn("Gesprek afgerond", self.thread.last_handoff_note)
        self.assertIn("Afsluitsignaal: opvolging_nodig", self.thread.last_handoff_note)
        self.assertEqual(self.thread.open_loop, "Morgen opvolgen of klant heeft gereageerd.")
        self.assertIsNotNone(self.thread.last_operator_handoff_at)
        self.assertContains(response, "Handoff opgeslagen")
        self.assertContains(response, "Morgen opvolgen of klant heeft gereageerd.")
        self.assertContains(response, "Top chat focus")

    def test_chat_hub_scan_context_is_present_in_template_and_context(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Top chat focus")
        self.assertContains(response, "Creator")
        self.assertContains(response, "Thread")
        self.assertContains(response, "Threadsamenvatting")
        self.assertContains(response, "Laatste statusmoment")
        self.assertContains(response, "Laatste handoff")
        self.assertIn("chat_focus_items", response.context)
        self.assertIn("latest_handoff_scan", response.context)
        self.assertIn("next_step_scan", response.context)
        self.assertTrue(response.context["chat_focus_items"])
        self.assertEqual(
            response.context["latest_handoff_scan"]["summary"],
            "Need manual approval before final reply.",
        )
        self.assertEqual(
            response.context["next_step_scan"],
            "Reply with updated delivery date.",
        )

    def test_chat_hub_scan_context_fallback_without_thread(self):
        ConversationThread.objects.filter(creator=self.creator).delete()
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["chat_focus_items"], [])
        self.assertEqual(
            response.context["latest_handoff_scan"]["summary"],
            "Geen actieve handoff beschikbaar zonder thread.",
        )
        self.assertEqual(
            response.context["next_step_scan"],
            "Nog geen volgende stap beschikbaar zonder thread.",
        )
        self.assertContains(response, "Selecteer een thread om het werkvlak te starten.")

    def test_chat_right_column_handoff_and_issues_are_directly_scannable(self):
        self.thread.risk_flags = "High-risk sentiment requires review."
        self.thread.save(update_fields=["risk_flags"])
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertContains(response, "<strong>Scan:</strong>", html=True)
        self.assertContains(response, "Need manual approval before final reply.")
        self.assertContains(response, "High-risk sentiment requires review.")
        self.assertContains(response, "Open loop: Reply with updated delivery date.")

    def test_blocked_state_rejects_handoff_submit_and_keeps_values(self):
        self.client.force_login(self.admin_user)
        old_note = self.thread.last_handoff_note
        response = self.client.post(
            reverse("chat-hub"),
            {
                "thread": str(self.thread.pk),
                "handoff_summary": "Dit mag niet opgeslagen worden.",
                "next_step": "Geen",
                "blocker": "Nog iets",
                "close_signal": "review_nodig",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.last_handoff_note, old_note)
        self.assertContains(response, "Handoff afsluiten is geblokkeerd")
        self.assertContains(response, "Dit mag niet opgeslagen worden.")
        self.assertContains(response, 'name="next_step" value="Geen"')
        self.assertContains(response, 'name="blocker" value="Nog iets"')
        self.assertContains(response, 'option value="review_nodig" selected')
