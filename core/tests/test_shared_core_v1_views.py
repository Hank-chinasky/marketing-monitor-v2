from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import (
    BuddyDraft,
    ConversationThread,
    Creator,
    CreatorChannel,
    CreatorMaterial,
    Operator,
    OperatorAssignment,
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
            content_source_url="https://example.com/source",
            content_ready_status=Creator.ContentReadyStatus.READY_TO_POST,
        )
        self.channel = CreatorChannel.objects.create(
            creator=self.creator,
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="shared-core-channel",
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

    def test_feeder_keeps_operator_first_four_center_blocks(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("feeder-hub"))

        self.assertContains(response, "Wat live moet")
        self.assertContains(response, "Wat aandacht nodig heeft")
        self.assertContains(response, "Door naar Chats")
        self.assertContains(response, "Ritme / opvolging")

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

    def test_buddy_slot_is_visible_and_renders_without_crash(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buddy-slot")
        self.assertContains(response, "Korte threadsamenvatting")
        self.assertContains(response, "Ontbrekende velden/contextgaten")
        self.assertContains(response, "Voorgestelde volgende stap")
        self.assertContains(response, "Compacte sessiebrief")

    def test_buddy_slot_handles_missing_handoff_and_context(self):
        self.thread.thread_summary = ""
        self.thread.open_loop = ""
        self.thread.last_handoff_note = ""
        self.thread.save(update_fields=["thread_summary", "open_loop", "last_handoff_note"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Threadsamenvatting ontbreekt.")
        self.assertContains(response, "Voorgestelde volgende stap ontbreekt.")
        self.assertContains(response, "Gecondenseerde laatste handoff:</strong> Niet beschikbaar.")

    def test_buddy_slot_shows_condensed_handoff_when_available(self):
        self.thread.thread_summary = "Klant vraagt om terugkoppeling op de status."
        self.thread.open_loop = "Stuur bevestiging en vraag om voorkeursmoment."
        self.thread.last_handoff_note = (
            "Laatste stand: klant heeft update gelezen en wacht op bevestiging. "
            "Volgende stap: korte bevestiging sturen met haalbare timing."
        )
        self.thread.save(update_fields=["thread_summary", "open_loop", "last_handoff_note"])

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Klant vraagt om terugkoppeling op de status.")
        self.assertContains(response, "Stuur bevestiging en vraag om voorkeursmoment.")
        self.assertContains(response, "Gecondenseerde laatste handoff")
        self.assertContains(response, "Laatste stand: klant heeft update gelezen")

    def test_buddy_slot_get_is_read_only_without_status_writes_or_side_effects(self):
        before_open_loop = self.thread.open_loop
        before_handoff = self.thread.last_handoff_note
        before_status = self.thread.status
        before_handoff_at = self.thread.last_operator_handoff_at
        before_material_count = CreatorMaterial.objects.count()

        self.client.force_login(self.user)
        response = self.client.get(reverse("chat-hub"), {"thread": self.thread.pk})

        self.assertEqual(response.status_code, 200)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.open_loop, before_open_loop)
        self.assertEqual(self.thread.last_handoff_note, before_handoff)
        self.assertEqual(self.thread.status, before_status)
        self.assertEqual(self.thread.last_operator_handoff_at, before_handoff_at)
        self.assertEqual(CreatorMaterial.objects.count(), before_material_count)
        self.assertNotContains(response, "Feeder content readiness check")
