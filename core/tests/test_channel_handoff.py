from django.test import SimpleTestCase
from django.utils import timezone

from core.forms import ChannelHandoffForm, CreatorChannelForm
from core.models import CreatorChannel


class ChannelHandoffFormTests(SimpleTestCase):
    def _build_channel(self):
        channel = CreatorChannel(
            platform=CreatorChannel.Platform.INSTAGRAM,
            handle="creator-one",
            status=CreatorChannel.Status.ACTIVE,
            access_mode=CreatorChannel.AccessMode.OPERATOR_DIRECT,
            recovery_owner=CreatorChannel.RecoveryOwner.CREATOR,
            session_what_done="Bio bijgewerkt.",
            session_next_action="Nieuwe caption klaarzetten.",
            session_blockers="Story assets ontbreken nog.",
            session_policy_context_reviewed=True,
        )
        channel.session_updated_at = timezone.now()
        return channel

    def test_form_requires_structured_fields(self):
        form = ChannelHandoffForm(
            data={
                "session_blockers": "Nog geen toegang tot stories.",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("session_what_done", form.errors)
        self.assertIn("session_next_action", form.errors)
        self.assertIn("session_policy_context_reviewed", form.errors)

    def test_form_strips_structured_values(self):
        form = ChannelHandoffForm(
            data={
                "session_what_done": "  Bio aangepast.  ",
                "session_next_action": "  Morgen story plaatsen.  ",
                "session_blockers": "  Wacht op asset.  ",
                "session_policy_context_reviewed": "on",
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["session_what_done"], "Bio aangepast.")
        self.assertEqual(form.cleaned_data["session_next_action"], "Morgen story plaatsen.")
        self.assertEqual(form.cleaned_data["session_blockers"], "Wacht op asset.")

    def test_form_prefills_from_structured_channel_fields(self):
        channel = self._build_channel()

        form = ChannelHandoffForm(channel=channel)

        self.assertEqual(form.initial["session_what_done"], "Bio bijgewerkt.")
        self.assertEqual(form.initial["session_next_action"], "Nieuwe caption klaarzetten.")
        self.assertEqual(form.initial["session_blockers"], "Story assets ontbreken nog.")
        self.assertTrue(form.initial["session_policy_context_reviewed"])

    def test_channel_builds_legacy_summary_from_structured_session(self):
        channel = self._build_channel()
        summary = channel.build_workspace_session_summary()

        self.assertIn("Wat gedaan:\nBio bijgewerkt.", summary)
        self.assertIn("Next action:\nNieuwe caption klaarzetten.", summary)
        self.assertIn("Blockers / open issues:\nStory assets ontbreken nog.", summary)
        self.assertIn("Policy/disclosure context reviewed: Ja", summary)

    def test_creator_channel_form_hides_legacy_handoff_fields(self):
        form = CreatorChannelForm()

        self.assertNotIn("last_operator_update", form.fields)
        self.assertNotIn("last_operator_update_at", form.fields)