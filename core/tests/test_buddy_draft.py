from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import BuddyDraft, ConversationThread, Creator, Operator


class BuddyDraftTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.operator_user = User.objects.create_user(
            username="operator-buddy-draft",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)
        self.creator = Creator.objects.create(
            display_name="Buddy Draft Creator",
            legal_name="Buddy Draft Creator BV",
            status=Creator.Status.ACTIVE,
            consent_status=Creator.ConsentStatus.ACTIVE,
        )
        self.thread = ConversationThread.objects.create(
            creator=self.creator,
            source_thread_id="mara-thread-1",
        )

    def make_draft(self, **overrides):
        payload = {
            "thread": self.thread,
            "reply_text": "Dank je, ik pak dit voor je op.",
            "intent": "follow_up",
            "tone": "warm",
            "confidence": Decimal("0.875"),
            "risk_level": BuddyDraft.RiskLevel.LOW,
            "generation_source": BuddyDraft.GenerationSource.STUB,
            "created_for_operator": self.operator,
        }
        payload.update(overrides)
        return BuddyDraft.objects.create(**payload)

    def test_buddy_draft_can_be_created(self):
        draft = self.make_draft()

        self.assertEqual(draft.thread, self.thread)
        self.assertEqual(draft.state, BuddyDraft.State.DRAFTED)
        self.assertEqual(draft.risk_level, BuddyDraft.RiskLevel.LOW)
        self.assertEqual(draft.generation_source, BuddyDraft.GenerationSource.STUB)
        self.assertEqual(draft.created_for_operator, self.operator)

    def test_thread_is_required(self):
        draft = BuddyDraft(
            reply_text="Klaar voor review.",
            intent="follow_up",
            tone="calm",
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

        with self.assertRaises(ValidationError) as ctx:
            draft.full_clean()

        self.assertIn("thread", ctx.exception.message_dict)

    def test_state_choices_validate_via_full_clean(self):
        draft = BuddyDraft(
            thread=self.thread,
            reply_text="Klaar voor review.",
            intent="follow_up",
            tone="calm",
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
            state="queued",
        )

        with self.assertRaises(ValidationError):
            draft.full_clean()

    def test_risk_level_choices_validate_via_full_clean(self):
        draft = BuddyDraft(
            thread=self.thread,
            reply_text="Klaar voor review.",
            intent="follow_up",
            tone="calm",
            risk_level="critical",
            generation_source=BuddyDraft.GenerationSource.STUB,
        )

        with self.assertRaises(ValidationError):
            draft.full_clean()

    def test_generation_source_choices_validate_via_full_clean(self):
        draft = BuddyDraft(
            thread=self.thread,
            reply_text="Klaar voor review.",
            intent="follow_up",
            tone="calm",
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source="other_api",
        )

        with self.assertRaises(ValidationError):
            draft.full_clean()

    def test_edited_after_generation_default_is_false(self):
        draft = self.make_draft()

        self.assertFalse(draft.edited_after_generation)

    def test_requires_human_attention_default_is_true(self):
        draft = self.make_draft()

        self.assertTrue(draft.requires_human_attention)

    def test_created_for_operator_can_be_stored(self):
        draft = self.make_draft(created_for_operator=self.operator)

        draft.refresh_from_db()
        self.assertEqual(draft.created_for_operator, self.operator)

    def test_simple_state_update_on_model_level_works(self):
        draft = self.make_draft()

        draft.state = BuddyDraft.State.APPROVED
        draft.save(update_fields=["state"])
        draft.refresh_from_db()

        self.assertEqual(draft.state, BuddyDraft.State.APPROVED)
        self.assertTrue(draft.is_approved())
        self.assertFalse(draft.is_drafted())
        self.assertFalse(draft.is_rejected())

    def test_confidence_can_be_empty(self):
        draft = BuddyDraft(
            thread=self.thread,
            reply_text="Klaar voor review.",
            intent="follow_up",
            tone="calm",
            confidence=None,
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )
        draft.full_clean()
        draft.save()

        draft.refresh_from_db()
        self.assertIsNone(draft.confidence)

    def test_confidence_accepts_valid_decimal_value(self):
        draft = BuddyDraft(
            thread=self.thread,
            reply_text="Klaar voor review.",
            intent="follow_up",
            tone="calm",
            confidence=Decimal("0.875"),
            risk_level=BuddyDraft.RiskLevel.MEDIUM,
            generation_source=BuddyDraft.GenerationSource.STUB,
        )
        draft.full_clean()
        draft.save()

        draft.refresh_from_db()
        self.assertEqual(draft.confidence, Decimal("0.875"))