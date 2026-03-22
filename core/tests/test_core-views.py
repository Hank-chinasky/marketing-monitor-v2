from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Creator, CreatorChannel, Operator, OperatorAssignment

User = get_user_model()


class BaseDataMixin:
    admin_password = "testpass123"
    operator_password = "testpass123"

    def make_admin(self, username="admin"):
        return User.objects.create_user(
            username=username,
            password=self.admin_password,
            is_staff=True,
            is_superuser=True,
        )

    def make_operator_user(self, username="operator1"):
        user = User.objects.create_user(
            username=username,
            password=self.operator_password,
        )
        operator = Operator.objects.create(user=user)
        return user, operator

    def make_creator(
        self,
        display_name="Creator A",
        status="active",
        consent_status="active",
        primary_operator=None,
    ):
        return Creator.objects.create(
            display_name=display_name,
            status=status,
            consent_status=consent_status,
            primary_operator=primary_operator,
        )

    def make_channel(
        self,
        creator,
        handle="creator_a",
        platform="instagram",
        status="active",
        access_mode="operator_direct",
        recovery_owner="agency",
        credential_status="",
        two_factor_enabled=False,
        vpn_required=False,
        approved_ip_label="",
        approved_egress_ip="",
        last_operator_update="",
        last_operator_update_at=None,
    ):
        return CreatorChannel.objects.create(
            creator=creator,
            platform=platform,
            handle=handle,
            status=status,
            access_mode=access_mode,
            recovery_owner=recovery_owner,
            credential_status=credential_status,
            two_factor_enabled=two_factor_enabled,
            vpn_required=vpn_required,
            approved_ip_label=approved_ip_label,
            approved_egress_ip=approved_egress_ip,
            last_operator_update=last_operator_update,
            last_operator_update_at=last_operator_update_at,
        )

    def assign_operator(
        self,
        operator,
        creator,
        scope="full_management",
        starts_at=None,
        ends_at=None,
        active=True,
    ):
        now = timezone.now()
        return OperatorAssignment.objects.create(
            operator=operator,
            creator=creator,
            scope=scope,
            starts_at=starts_at or (now - timedelta(days=1)),
            ends_at=ends_at or (now + timedelta(days=7)),
            active=active,
        )


class CreatorModelTests(BaseDataMixin, TestCase):
    def test_creator_str_returns_display_name(self):
        creator = self.make_creator(display_name="Creator Alpha")
        self.assertEqual(str(creator), "Creator Alpha")


class CreatorChannelModelTests(BaseDataMixin, TestCase):
    def test_channel_str_contains_creator_platform_and_handle(self):
        creator = self.make_creator(display_name="Creator Alpha")
        channel = self.make_channel(
            creator=creator,
            platform="instagram",
            handle="alpha_handle",
        )
        self.assertEqual(
            str(channel),
            "Creator Alpha / instagram / alpha_handle",
        )


class DashboardViewTests(BaseDataMixin, TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_renders_for_admin(self):
        admin = self.make_admin()
        creator = self.make_creator()
        self.make_channel(creator=creator, credential_status="needs_reset")

        self.client.login(username=admin.username, password=self.admin_password)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)


class ChannelDetailViewTests(BaseDataMixin, TestCase):
    def test_channel_detail_renders_for_admin(self):
        admin = self.make_admin()
        creator = self.make_creator(display_name="Creator Detail")
        channel = self.make_channel(
            creator=creator,
            handle="detail_handle",
            last_operator_update="Laatste contextregel",
        )

        self.client.login(username=admin.username, password=self.admin_password)
        response = self.client.get(reverse("channel-detail", kwargs={"pk": channel.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laatste contextregel")
        self.assertContains(response, "Creator Detail")

    def test_assigned_operator_can_view_scoped_channel_detail(self):
        creator = self.make_creator(display_name="Scoped Creator")
        channel = self.make_channel(creator=creator, handle="scoped_handle")
        operator_user, operator = self.make_operator_user()
        self.assign_operator(operator=operator, creator=creator)

        self.client.login(
            username=operator_user.username,
            password=self.operator_password,
        )
        response = self.client.get(reverse("channel-detail", kwargs={"pk": channel.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "scoped_handle")