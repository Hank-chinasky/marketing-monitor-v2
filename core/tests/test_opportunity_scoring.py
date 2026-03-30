from django.test import SimpleTestCase

from core.models import ProfileOpportunity
from core.services.opportunity_scoring import evaluate_opportunity


class OpportunityScoringTests(SimpleTestCase):
    def test_risk_minus_two_is_hard_catch(self):
        result = evaluate_opportunity(
            source_quality_score=2,
            profile_signal_score=2,
            intent_guess_score=2,
            target_fit_score=2,
            risk_penalty_score=-2,
        )
        self.assertEqual(result.priority_band, ProfileOpportunity.PriorityBand.LOW)
        self.assertEqual(result.action_bucket, ProfileOpportunity.ActionBucket.NOT_WORTH)

    def test_fit_zero_and_intent_zero_is_hard_catch(self):
        result = evaluate_opportunity(
            source_quality_score=2,
            profile_signal_score=2,
            intent_guess_score=0,
            target_fit_score=0,
            risk_penalty_score=0,
        )
        self.assertEqual(result.priority_band, ProfileOpportunity.PriorityBand.LOW)
        self.assertEqual(result.action_bucket, ProfileOpportunity.ActionBucket.NOT_WORTH)

    def test_total_score_seven_becomes_high(self):
        result = evaluate_opportunity(
            source_quality_score=2,
            profile_signal_score=2,
            intent_guess_score=1,
            target_fit_score=2,
            risk_penalty_score=0,
        )
        self.assertEqual(result.total_score, 7)
        self.assertEqual(result.priority_band, ProfileOpportunity.PriorityBand.HIGH)
        self.assertEqual(result.action_bucket, ProfileOpportunity.ActionBucket.NOW)

    def test_total_score_five_becomes_medium(self):
        result = evaluate_opportunity(
            source_quality_score=1,
            profile_signal_score=1,
            intent_guess_score=1,
            target_fit_score=2,
            risk_penalty_score=0,
        )
        self.assertEqual(result.total_score, 5)
        self.assertEqual(result.priority_band, ProfileOpportunity.PriorityBand.MEDIUM)
        self.assertEqual(result.action_bucket, ProfileOpportunity.ActionBucket.LATER)

    def test_total_score_three_becomes_low(self):
        result = evaluate_opportunity(
            source_quality_score=1,
            profile_signal_score=1,
            intent_guess_score=0,
            target_fit_score=1,
            risk_penalty_score=0,
        )
        self.assertEqual(result.total_score, 3)
        self.assertEqual(result.priority_band, ProfileOpportunity.PriorityBand.LOW)
        self.assertEqual(result.action_bucket, ProfileOpportunity.ActionBucket.NOT_WORTH)

    def test_rule_a_upgrades_six_with_strong_intent(self):
        result = evaluate_opportunity(
            source_quality_score=2,
            profile_signal_score=2,
            intent_guess_score=2,
            target_fit_score=1,
            risk_penalty_score=-1,
        )
        self.assertEqual(result.total_score, 6)
        self.assertEqual(result.priority_band, ProfileOpportunity.PriorityBand.HIGH)
        self.assertEqual(result.action_bucket, ProfileOpportunity.ActionBucket.NOW)

    def test_rule_b_blocks_high_when_fit_is_zero(self):
        result = evaluate_opportunity(
            source_quality_score=2,
            profile_signal_score=2,
            intent_guess_score=2,
            target_fit_score=0,
            risk_penalty_score=0,
        )
        self.assertEqual(result.total_score, 6)
        self.assertEqual(result.priority_band, ProfileOpportunity.PriorityBand.MEDIUM)
        self.assertEqual(result.action_bucket, ProfileOpportunity.ActionBucket.LATER)

    def test_rule_d_blocks_now_when_only_source_is_strong(self):
        result = evaluate_opportunity(
            source_quality_score=2,
            profile_signal_score=0,
            intent_guess_score=0,
            target_fit_score=2,
            risk_penalty_score=0,
        )
        self.assertEqual(result.total_score, 4)
        self.assertEqual(result.priority_band, ProfileOpportunity.PriorityBand.MEDIUM)
        self.assertEqual(result.action_bucket, ProfileOpportunity.ActionBucket.LATER)

    def test_score_reason_short_stays_functional(self):
        result = evaluate_opportunity(
            source_quality_score=2,
            profile_signal_score=1,
            intent_guess_score=1,
            target_fit_score=1,
            risk_penalty_score=-1,
        )
        self.assertIn("Sterke bron", result.score_reason_short)
        self.assertIn("beperkt risico", result.score_reason_short)
