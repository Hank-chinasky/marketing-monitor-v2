from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.views import View

from core.mixins import AdminDeleteOnlyMixin
from core.models import Creator, CreatorChannel, Operator, OperatorAssignment
from core.services.scope import (
    get_channel_queryset_for_user,
    get_creator_queryset_for_user,
    user_can_access_channel,
    user_can_access_creator,
)
from core.validators import validate_no_overlapping_assignments


class BaseScopeTestCase(TestCase):
    def setUp(self):
        User = get_user_model()

        self.admin = User.objects.create_user(
            username="admin",
            password="x",
            is_active=True,
            is_staff=True,
        )

        self.operator_user = User.objects.create_user(
            username="operator",
            password="x",
            is_active=True,
        )
        self.operator = Operator.objects.create(user=self.operator_user)

        self.second_operator_user = User.objects.create_user(
            username="operator2",
            password="x",
            is_active=True,
        )
        self.second_operator = Operator.objects.create(user=self.second_operator_user)

        self.unassigned_operator_user = User.objects.create_user(
            username="unassigned-operator",
            password="x",
            is_active=True,
        )
        self.unassigned_operator = Operator.objects.create(user=self.unassigned_operator_user)

        self.plain_user = User.objects.create_user(
            username="plain-user",
            password="x",
            is_active=True,
        )

        self.creator_a = Creator.objects.create(
            display_name="Creator A",
            legal_name="Creator A BV",
            status="active",
            consent_status="active",
        )
        self.creator_b = Creator.objects.create(
            display_name="Creator B",
            legal_name="Creator B BV",
            status="active",
            consent_status="active",
        )
        self.creator_c = Creator.objects.create(
            display_name="Creator C",
            legal_name="Creator C BV",
            status="active",
            consent_status="active",
        )

        self.channel_a = CreatorChannel.objects.create(
            creator=self.creator_a,
            platform="tiktok",
            handle="creator-a",
            access_mode="creator_only",
            recovery_owner="creator",
            status="active",
            credential_status="known",
        )
        self.channel_b = CreatorChannel.objects.create(
            creator=self.creator_b,
            platform="instagram",
            handle="creator-b",
            access_mode="creator_only",
            recovery_owner="creator",
            status="active",
            credential_status="known",
        )
        self.channel_c = CreatorChannel.objects.create(
            creator=self.creator_c,
            platform="telegram",
            handle="creator-c",
            access_mode="creator_only",
            recovery_owner="creator",
            status="active",
            credential_status="known",
        )

        now = timezone.now()
        self.assignment_a = OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator_a,
            scope="full_management",
            starts_at=now - timedelta(days=1),
            ends_at=None,
            active=True,
        )
        self.assignment_b = OperatorAssignment.objects.create(
            operator=self.second_operator,
            creator=self.creator_b,
            scope="full_management",
            starts_at=now - timedelta(days=1),
            ends_at=None,
            active=True,
        )


class ScopeServiceTests(BaseScopeTestCase):
    def test_admin_sees_all_creators(self):
        qs = get_creator_queryset_for_user(self.admin)
        self.assertEqual(set(qs), {self.creator_a, self.creator_b, self.creator_c})

    def test_admin_sees_all_channels(self):
        qs = get_channel_queryset_for_user(self.admin)
        self.assertEqual(set(qs), {self.channel_a, self.channel_b, self.channel_c})

    def test_operator_sees_only_assigned_creators(self):
        qs = get_creator_queryset_for_user(self.operator_user)
        self.assertEqual(set(qs), {self.creator_a})

    def test_operator_sees_only_channels_of_assigned_creators(self):
        qs = get_channel_queryset_for_user(self.operator_user)
        self.assertEqual(set(qs), {self.channel_a})

    def test_operator_without_assignment_sees_nothing_operationally(self):
        self.assertEqual(get_creator_queryset_for_user(self.unassigned_operator_user).count(), 0)
        self.assertEqual(get_channel_queryset_for_user(self.unassigned_operator_user).count(), 0)

    def test_user_without_operator_profile_sees_nothing_operationally(self):
        self.assertEqual(get_creator_queryset_for_user(self.plain_user).count(), 0)
        self.assertEqual(get_channel_queryset_for_user(self.plain_user).count(), 0)

    def test_inactive_assignment_gives_no_access(self):
        self.assignment_a.active = False
        self.assignment_a.save()

        self.assertEqual(get_creator_queryset_for_user(self.operator_user).count(), 0)
        self.assertEqual(get_channel_queryset_for_user(self.operator_user).count(), 0)

    def test_future_assignment_gives_no_access(self):
        self.assignment_a.starts_at = timezone.now() + timedelta(days=1)
        self.assignment_a.save()

        self.assertEqual(get_creator_queryset_for_user(self.operator_user).count(), 0)
        self.assertEqual(get_channel_queryset_for_user(self.operator_user).count(), 0)

    def test_expired_assignment_gives_no_access(self):
        self.assignment_a.ends_at = timezone.now() - timedelta(minutes=1)
        self.assignment_a.save()

        self.assertEqual(get_creator_queryset_for_user(self.operator_user).count(), 0)
        self.assertEqual(get_channel_queryset_for_user(self.operator_user).count(), 0)

    def test_primary_operator_without_assignment_gives_no_access(self):
        self.creator_c.primary_operator = self.operator
        self.creator_c.save()

        self.assertFalse(user_can_access_creator(self.operator_user, self.creator_c))
        self.assertFalse(user_can_access_channel(self.operator_user, self.channel_c))
        self.assertEqual(set(get_creator_queryset_for_user(self.operator_user)), {self.creator_a})

    def test_operator_with_two_assignments_sees_both_and_only_those(self):
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator_c,
            scope="posting_only",
            starts_at=timezone.now() - timedelta(days=1),
            ends_at=None,
            active=True,
        )

        creator_qs = get_creator_queryset_for_user(self.operator_user)
        channel_qs = get_channel_queryset_for_user(self.operator_user)

        self.assertEqual(set(creator_qs), {self.creator_a, self.creator_c})
        self.assertEqual(set(channel_qs), {self.channel_a, self.channel_c})

    def test_assignment_with_end_exactly_now_is_still_active(self):
        frozen_now = timezone.now()

        exact_creator = Creator.objects.create(
            display_name="Creator Exact",
            legal_name="Creator Exact BV",
            status="active",
            consent_status="active",
        )
        exact_channel = CreatorChannel.objects.create(
            creator=exact_creator,
            platform="other",
            handle="creator-exact",
            access_mode="creator_only",
            recovery_owner="creator",
            status="active",
            credential_status="known",
        )

        with patch("core.services.scope.timezone.now", return_value=frozen_now):
            OperatorAssignment.objects.create(
                operator=self.operator,
                creator=exact_creator,
                scope="full_management",
                starts_at=frozen_now - timedelta(days=1),
                ends_at=frozen_now,
                active=True,
            )

            self.assertTrue(
                get_creator_queryset_for_user(self.operator_user).filter(pk=exact_creator.pk).exists()
            )
            self.assertTrue(
                get_channel_queryset_for_user(self.operator_user).filter(pk=exact_channel.pk).exists()
            )

    def test_overlap_rule_blocks_overlaps_for_same_creator_across_operators(self):
        new_assignment = OperatorAssignment(
            operator=self.second_operator,
            creator=self.creator_a,
            scope="draft_only",
            starts_at=timezone.now() - timedelta(hours=12),
            ends_at=None,
            active=True,
        )

        with self.assertRaises(ValidationError):
            validate_no_overlapping_assignments(new_assignment)


class ScopeViewTests(BaseScopeTestCase):
    def test_admin_can_open_creator_detail(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator_a.pk}))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_open_creator_edit(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("creator-update", kwargs={"pk": self.creator_a.pk}))
        self.assertEqual(response.status_code, 200)

    def test_operator_can_open_assigned_creator_detail(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator_a.pk}))
        self.assertEqual(response.status_code, 200)

    def test_operator_gets_404_on_unassigned_creator_detail(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator_b.pk}))
        self.assertEqual(response.status_code, 404)

    def test_operator_gets_403_on_assigned_creator_edit(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("creator-update", kwargs={"pk": self.creator_a.pk}))
        self.assertEqual(response.status_code, 403)

    def test_operator_gets_403_on_unassigned_creator_edit(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("creator-update", kwargs={"pk": self.creator_b.pk}))
        self.assertEqual(response.status_code, 403)

    def test_plain_user_gets_404_on_creator_detail(self):
        self.client.force_login(self.plain_user)
        response = self.client.get(reverse("creator-detail", kwargs={"pk": self.creator_a.pk}))
        self.assertEqual(response.status_code, 404)

    def test_admin_can_open_channel_detail(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("channel-detail", kwargs={"pk": self.channel_a.pk}))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_open_channel_edit(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("channel-update", kwargs={"pk": self.channel_a.pk}))
        self.assertEqual(response.status_code, 200)

    def test_operator_can_open_assigned_channel_detail(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("channel-detail", kwargs={"pk": self.channel_a.pk}))
        self.assertEqual(response.status_code, 200)

    def test_operator_gets_404_on_unassigned_channel_detail(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("channel-detail", kwargs={"pk": self.channel_b.pk}))
        self.assertEqual(response.status_code, 404)

    def test_operator_gets_403_on_assigned_channel_edit(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("channel-update", kwargs={"pk": self.channel_a.pk}))
        self.assertEqual(response.status_code, 403)

    def test_operator_gets_403_on_unassigned_channel_edit(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("channel-update", kwargs={"pk": self.channel_b.pk}))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_for_admin_shows_full_counts(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("operations-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["creator_count"], 3)
        self.assertEqual(response.context["summary"]["channel_count"], 3)
        self.assertEqual(response.context["summary"]["assignment_count"], 2)

    def test_dashboard_for_operator_shows_only_scoped_counts(self):
        self.client.force_login(self.operator_user)
        response = self.client.get(reverse("operations-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["creator_count"], 1)
        self.assertEqual(response.context["summary"]["channel_count"], 1)
        self.assertEqual(response.context["summary"]["assignment_count"], 1)
        self.assertEqual([creator.pk for creator in response.context["my_creators"]], [self.creator_a.pk])
        self.assertEqual([channel.pk for channel in response.context["quick_channels"]], [self.channel_a.pk])

    def test_dashboard_for_plain_user_shows_no_operational_data(self):
        self.client.force_login(self.plain_user)
        response = self.client.get(reverse("operations-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["creator_count"], 0)
        self.assertEqual(response.context["summary"]["channel_count"], 0)
        self.assertEqual(response.context["summary"]["assignment_count"], 0)
        self.assertEqual(response.context["my_creators"], [])
        self.assertEqual(response.context["quick_channels"], [])


class DummyDeleteView(AdminDeleteOnlyMixin, View):
    def post(self, request, *args, **kwargs):
        return HttpResponse("ok")


class DeleteScopeTests(BaseScopeTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_admin_delete_only_mixin_allows_admin(self):
        request = self.factory.post("/dummy-delete/")
        request.user = self.admin

        response = DummyDeleteView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_admin_delete_only_mixin_blocks_operator(self):
        request = self.factory.post("/dummy-delete/")
        request.user = self.operator_user

        with self.assertRaises(PermissionDenied):
            DummyDeleteView.as_view()(request)

    def test_creator_delete_route_does_not_exist_in_current_runtime(self):
        with self.assertRaises(NoReverseMatch):
            reverse("creator-delete")

    def test_channel_delete_route_does_not_exist_in_current_runtime(self):
        with self.assertRaises(NoReverseMatch):
            reverse("channel-delete")
