from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.authz import (
    can_view_creator,
    is_active_internal_user,
    is_admin,
    scope_assignments_queryset,
    scope_channels_queryset,
    scope_creators_queryset,
)
from core.models import Creator, CreatorChannel, Operator, OperatorAssignment
from core.validators import validate_no_overlapping_assignments


class ScopeAuthTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.admin = User.objects.create_user(username="admin", password="x")
        self.admin.is_staff = True
        self.admin.is_active = True
        self.admin.save()

        self.operator_user = User.objects.create_user(username="op", password="x")
        self.operator_user.is_active = True
        self.operator_user.save()
        self.operator = Operator.objects.create(user=self.operator_user)

        self.other_user = User.objects.create_user(username="other", password="x")
        self.other_user.is_active = True
        self.other_user.save()

        self.creator_in = Creator.objects.create(display_name="in-scope", status="active", consent_status="active")
        self.creator_out = Creator.objects.create(display_name="out-of-scope", status="active", consent_status="active")

        self.channel_in = CreatorChannel.objects.create(
            creator=self.creator_in,
            platform="tiktok",
            handle="InHandle",
            access_mode="creator_only",
            recovery_owner="creator",
            status="active",
        )
        self.channel_out = CreatorChannel.objects.create(
            creator=self.creator_out,
            platform="tiktok",
            handle="OutHandle",
            access_mode="creator_only",
            recovery_owner="creator",
            status="active",
        )

        now = timezone.now()
        self.assignment_active = OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator_in,
            starts_at=now - timedelta(days=1),
            ends_at=None,
            active=True,
        )

    def test_admin_sees_all_creators(self):
        qs = scope_creators_queryset(self.admin)
        self.assertEqual(set(qs), {self.creator_in, self.creator_out})

    def test_operator_sees_only_in_scope_creators(self):
        qs = scope_creators_queryset(self.operator_user)
        self.assertEqual(set(qs), {self.creator_in})

    def test_operator_cannot_see_out_of_scope_creator(self):
        self.assertTrue(can_view_creator(self.operator_user, self.creator_in))
        self.assertFalse(can_view_creator(self.operator_user, self.creator_out))

    def test_user_without_operator_profile_sees_no_operational_records(self):
        self.assertEqual(scope_creators_queryset(self.other_user).count(), 0)
        self.assertEqual(scope_channels_queryset(self.other_user).count(), 0)
        self.assertEqual(scope_assignments_queryset(self.other_user).count(), 0)

    def test_inactive_user_is_not_active_internal_user(self):
        User = get_user_model()
        u = User.objects.create_user(username="inactive", password="x")
        u.is_active = False
        u.save()

        self.assertFalse(is_active_internal_user(u))
        self.assertEqual(scope_creators_queryset(u).count(), 0)

    def test_inactive_staff_user_is_not_admin(self):
        User = get_user_model()
        u = User.objects.create_user(username="inactive_staff", password="x")
        u.is_staff = True
        u.is_active = False
        u.save()

        self.assertFalse(is_active_internal_user(u))
        self.assertFalse(is_admin(u))
        self.assertEqual(scope_creators_queryset(u).count(), 0)

    def test_expired_assignment_gives_no_visibility(self):
        self.assignment_active.ends_at = timezone.now() - timedelta(hours=1)
        self.assignment_active.save()

        self.assertEqual(scope_creators_queryset(self.operator_user).count(), 0)

    def test_future_assignment_gives_no_visibility_yet(self):
        OperatorAssignment.objects.all().delete()
        now = timezone.now()
        OperatorAssignment.objects.create(
            operator=self.operator,
            creator=self.creator_in,
            starts_at=now + timedelta(days=1),
            ends_at=None,
            active=True,
        )
        self.assertEqual(scope_creators_queryset(self.operator_user).count(), 0)

    def test_overlap_rule_blocks_overlaps_for_same_creator_across_operators(self):
        User = get_user_model()
        u2 = User.objects.create_user(username="op2", password="x")
        u2.is_active = True
        u2.save()
        op2 = Operator.objects.create(user=u2)

        now = timezone.now()
        new_assignment = OperatorAssignment(
            operator=op2,
            creator=self.creator_in,
            starts_at=now - timedelta(hours=12),
            ends_at=None,
            active=True,
        )

        with self.assertRaises(ValidationError):
            validate_no_overlapping_assignments(new_assignment)

    def test_primary_operator_without_assignment_gives_no_scope(self):
        OperatorAssignment.objects.all().delete()
        self.creator_out.primary_operator = self.operator
        self.creator_out.save()

        self.assertEqual(scope_creators_queryset(self.operator_user).count(), 0)

    def test_channels_follow_creator_scope(self):
        qs = scope_channels_queryset(self.operator_user)
        self.assertEqual(set(qs), {self.channel_in})

    def test_assignments_follow_operator_scope(self):
        qs = scope_assignments_queryset(self.operator_user)
        self.assertEqual(set(qs), {self.assignment_active})
