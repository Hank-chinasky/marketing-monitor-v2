from django.contrib.auth import get_user_model
from django.test import TestCase

from core.forms import ProfileOpportunityForm
from core.models import ProfileOpportunity


class ProfileOpportunityFormTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin-opportunity-form",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator = user_model.objects.create_user(
            username="operator-opportunity-form",
            password="x",
            is_active=True,
        )

    def test_override_requires_reason(self):
        form = ProfileOpportunityForm(
            data={
                "assigned_to": self.operator.pk,
                "intake_name": "Test intake",
                "profile_url": "",
                "intake_notes": "",
                "handoff_note": "",
                "source_quality_score": 1,
                "profile_signal_score": 1,
                "intent_guess_score": 1,
                "target_fit_score": 1,
                "risk_penalty_score": 0,
                "manual_override": True,
                "override_priority_band": "high",
                "override_action_bucket": "nu_oppakken",
                "override_reason_short": "",
            },
            user=self.admin,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("override_reason_short", form.errors)

    def test_invalid_score_value_is_rejected(self):
        form = ProfileOpportunityForm(
            data={
                "assigned_to": self.operator.pk,
                "intake_name": "Test intake",
                "profile_url": "",
                "intake_notes": "",
                "handoff_note": "",
                "source_quality_score": 3,
                "profile_signal_score": 1,
                "intent_guess_score": 1,
                "target_fit_score": 1,
                "risk_penalty_score": 0,
                "manual_override": False,
                "override_priority_band": "",
                "override_action_bucket": "",
                "override_reason_short": "",
            },
            user=self.admin,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("source_quality_score", form.errors)

    def test_form_save_recomputes_scoring_output(self):
        form = ProfileOpportunityForm(
            data={
                "assigned_to": self.operator.pk,
                "intake_name": "Strong intake",
                "profile_url": "https://example.com/profile",
                "intake_notes": "Some notes",
                "handoff_note": "Some handoff",
                "source_quality_score": 2,
                "profile_signal_score": 2,
                "intent_guess_score": 2,
                "target_fit_score": 1,
                "risk_penalty_score": -1,
                "manual_override": False,
                "override_priority_band": "",
                "override_action_bucket": "",
                "override_reason_short": "",
            },
            user=self.admin,
        )
        self.assertTrue(form.is_valid(), form.errors)
        opportunity = form.save()

        self.assertEqual(opportunity.total_score, 6)
        self.assertEqual(opportunity.priority_band, ProfileOpportunity.PriorityBand.HIGH)
        self.assertEqual(opportunity.action_bucket, ProfileOpportunity.ActionBucket.NOW)

    def test_non_admin_cannot_reassign_assigned_to(self):
        opportunity = ProfileOpportunity.objects.create(
            assigned_to=self.operator,
            intake_name="Scoped intake",
            source_quality_score=1,
            profile_signal_score=1,
            intent_guess_score=1,
            target_fit_score=1,
            risk_penalty_score=0,
        )

        other_user = get_user_model().objects.create_user(
            username="other-opportunity-user",
            password="x",
            is_active=True,
        )

        form = ProfileOpportunityForm(
            data={
                "assigned_to": other_user.pk,
                "intake_name": "Scoped intake updated",
                "profile_url": "",
                "intake_notes": "",
                "handoff_note": "",
                "source_quality_score": 1,
                "profile_signal_score": 1,
                "intent_guess_score": 1,
                "target_fit_score": 1,
                "risk_penalty_score": 0,
                "manual_override": False,
                "override_priority_band": "",
                "override_action_bucket": "",
                "override_reason_short": "",
            },
            instance=opportunity,
            user=self.operator,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.assigned_to, self.operator)
