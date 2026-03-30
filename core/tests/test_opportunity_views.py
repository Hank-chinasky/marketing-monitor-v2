from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import OutcomeEntry, ProfileOpportunity


class OpportunityViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin-opportunity-views",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_a = user_model.objects.create_user(
            username="operator-a-opportunity-views",
            password="x",
            is_active=True,
        )
        self.operator_b = user_model.objects.create_user(
            username="operator-b-opportunity-views",
            password="x",
            is_active=True,
        )

        self.high_new = ProfileOpportunity.objects.create(
            assigned_to=self.operator_a,
            intake_name="High new",
            source_quality_score=2,
            profile_signal_score=2,
            intent_guess_score=1,
            target_fit_score=2,
            risk_penalty_score=0,
        )
        self.high_old = ProfileOpportunity.objects.create(
            assigned_to=self.operator_a,
            intake_name="High old",
            source_quality_score=2,
            profile_signal_score=2,
            intent_guess_score=1,
            target_fit_score=2,
            risk_penalty_score=0,
        )
        self.medium_item = ProfileOpportunity.objects.create(
            assigned_to=self.operator_a,
            intake_name="Medium item",
            source_quality_score=1,
            profile_signal_score=1,
            intent_guess_score=1,
            target_fit_score=2,
            risk_penalty_score=0,
        )
        self.low_override_high = ProfileOpportunity.objects.create(
            assigned_to=self.operator_a,
            intake_name="Override high",
            source_quality_score=1,
            profile_signal_score=1,
            intent_guess_score=0,
            target_fit_score=1,
            risk_penalty_score=0,
            manual_override=True,
            override_priority_band=ProfileOpportunity.PriorityBand.HIGH,
            override_action_bucket=ProfileOpportunity.ActionBucket.NOW,
            override_reason_short="Menselijke correctie",
        )
        self.other_user_item = ProfileOpportunity.objects.create(
            assigned_to=self.operator_b,
            intake_name="Other user item",
            source_quality_score=1,
            profile_signal_score=1,
            intent_guess_score=1,
            target_fit_score=1,
            risk_penalty_score=0,
        )

        now = timezone.now()
        ProfileOpportunity.objects.filter(pk=self.high_old.pk).update(updated_at=now - timedelta(days=1))
        ProfileOpportunity.objects.filter(pk=self.high_new.pk).update(updated_at=now - timedelta(hours=1))
        ProfileOpportunity.objects.filter(pk=self.medium_item.pk).update(updated_at=now - timedelta(minutes=30))
        ProfileOpportunity.objects.filter(pk=self.low_override_high.pk).update(updated_at=now - timedelta(minutes=10))

        self.high_old.refresh_from_db()
        self.high_new.refresh_from_db()
        self.medium_item.refresh_from_db()
        self.low_override_high.refresh_from_db()

    def test_admin_sees_all_opportunities(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("opportunity-queue"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "High new")
        self.assertContains(response, "Other user item")

    def test_operator_sees_only_assigned_opportunities(self):
        self.client.force_login(self.operator_a)
        response = self.client.get(reverse("opportunity-queue"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "High new")
        self.assertNotContains(response, "Other user item")

    def test_operator_cannot_open_other_users_opportunity(self):
        self.client.force_login(self.operator_a)
        response = self.client.get(
            reverse("opportunity-detail", kwargs={"pk": self.other_user_item.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_queue_orders_by_effective_priority_then_updated_at(self):
        self.client.force_login(self.operator_a)
        response = self.client.get(reverse("opportunity-queue"))
        self.assertEqual(response.status_code, 200)

        opportunities = list(response.context["opportunities"])
        ordered_names = [item.intake_name for item in opportunities]

        self.assertEqual(
            ordered_names,
            [
                "Override high",
                "High new",
                "High old",
                "Medium item",
            ],
        )

    def test_detail_save_recomputes_score(self):
        self.client.force_login(self.operator_a)
        response = self.client.post(
            reverse("opportunity-save", kwargs={"pk": self.medium_item.pk}),
            data={
                "assigned_to": self.operator_a.pk,
                "intake_name": "Medium item updated",
                "profile_url": "",
                "intake_notes": "Updated notes",
                "handoff_note": "Updated handoff",
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
        )
        self.assertEqual(response.status_code, 302)

        self.medium_item.refresh_from_db()
        self.assertEqual(self.medium_item.intake_name, "Medium item updated")
        self.assertEqual(self.medium_item.priority_band, ProfileOpportunity.PriorityBand.HIGH)
        self.assertEqual(self.medium_item.action_bucket, ProfileOpportunity.ActionBucket.NOW)

    def test_operator_can_add_outcome(self):
        self.client.force_login(self.operator_a)
        response = self.client.post(
            reverse("opportunity-outcome-add", kwargs={"pk": self.high_new.pk}),
            data={
                "outcome_type": OutcomeEntry.OutcomeType.GESPREK_GESTART,
                "notes": "Kort eerste contact",
            },
        )
        self.assertEqual(response.status_code, 302)

        outcome = OutcomeEntry.objects.get(opportunity=self.high_new)
        self.assertEqual(outcome.created_by, self.operator_a)
        self.assertEqual(outcome.outcome_type, OutcomeEntry.OutcomeType.GESPREK_GESTART)

    def test_queue_is_paginated_to_fifty(self):
        for index in range(60):
            ProfileOpportunity.objects.create(
                assigned_to=self.operator_a,
                intake_name=f"Paginated item {index}",
                source_quality_score=1,
                profile_signal_score=1,
                intent_guess_score=1,
                target_fit_score=1,
                risk_penalty_score=0,
            )

        self.client.force_login(self.operator_a)
        response = self.client.get(reverse("opportunity-queue"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["opportunities"]), 50)
