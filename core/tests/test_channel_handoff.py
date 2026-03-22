from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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
        login_identifier="creator_a_login",
        account_email="",
        account_phone_number="",
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
            login_identifier=login_identifier,
            account_email=account_email,
            account_phone_number=account_phone_number,
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


class CreatorChannelValidationTests(BaseDataMixin, TestCase):
    def test_vpn_required_needs_ip_label_or_egress_ip(self):
        creator = self.make_creator()

        channel = CreatorChannel(
            creator=creator,
            platform="instagram",
            handle="vpn_missing",
            status="active",
            access_mode="operator_direct",
            recovery_owner="agency",
            login_identifier="vpn_missing_login",
            vpn_required=True,
            approved_ip_label="",
            approved_egress_ip="",
        )

        with self.assertRaises(ValidationError) as ctx:
            channel.full_clean()

        self.assertIn("approved_ip_label", ctx.exception.message_dict)
        self.assertIn("approved_egress_ip", ctx.exception.message_dict)

    def test_vpn_required_with_ip_label_is_valid(self):
        creator = self.make_creator()

        channel = CreatorChannel(
            creator=creator,
            platform="instagram",
            handle="vpn_ok",
            status="active",
            access_mode="operator_direct",
            recovery_owner="agency",
            login_identifier="vpn_ok_login",
            vpn_required=True,
            approved_ip_label="ams-vpn-1",
            approved_egress_ip="",
        )

        channel.full_clean()

    def test_vpn_required_with_egress_ip_is_valid(self):
        creator = self.make_creator()

        channel = CreatorChannel(
            creator=creator,
            platform="instagram",
            handle="vpn_ok_ip",
            status="active",
            access_mode="operator_direct",
            recovery_owner="agency",
            login_identifier="vpn_ok_ip_login",
            vpn_required=True,
            approved_ip_label="",
            approved_egress_ip="203.0.113.15",
        )

        channel.full_clean()


class ChannelHandoffUpdateViewTests(BaseDataMixin, TestCase):
    def test_admin_update_sets_last_operator_update_at(self):
        admin = self.make_admin()
        creator = self.make_creator()
        channel = self.make_channel(creator=creator)

        self.client.login(username=admin.username, password=self.admin_password)

        response = self.client.post(
            reverse("channel-update", kwargs={"pk": channel.pk}),
            {
                "creator": creator.pk,
                "platform": channel.platform,
                "handle": channel.handle,
                "profile_url": "",
                "status": channel.status,
                "access_mode": channel.access_mode,
                "recovery_owner": channel.recovery_owner,
                "login_identifier": channel.login_identifier,
                "account_email": "",
                "account_phone_number": "",
                "credential_status": "",
                "access_notes": "",
                "last_access_check_at": "",
                "two_factor_enabled": "",
                "vpn_required": "",
                "approved_egress_ip": "",
                "approved_ip_label": "",
                "approved_access_region": "",
                "access_profile_notes": "",
                "last_ip_check_at": "",
                "last_operator_update": "Account checked, ready for follow-up.",
            },
        )

        self.assertEqual(response.status_code, 302)

        channel.refresh_from_db()
        self.assertEqual(
            channel.last_operator_update,
            "Account checked, ready for follow-up.",
        )
        self.assertIsNotNone(channel.last_operator_update_at)

    def test_clearing_last_operator_update_clears_timestamp(self):
        admin = self.make_admin()
        creator = self.make_creator()
        channel = self.make_channel(
            creator=creator,
            last_operator_update="Old note",
            last_operator_update_at=timezone.now(),
        )

        self.client.login(username=admin.username, password=self.admin_password)

        response = self.client.post(
            reverse("channel-update", kwargs={"pk": channel.pk}),
            {
                "creator": creator.pk,
                "platform": channel.platform,
                "handle": channel.handle,
                "profile_url": "",
                "status": channel.status,
                "access_mode": channel.access_mode,
                "recovery_owner": channel.recovery_owner,
                "login_identifier": channel.login_identifier,
                "account_email": "",
                "account_phone_number": "",
                "credential_status": "",
                "access_notes": "",
                "last_access_check_at": "",
                "two_factor_enabled": "",
                "vpn_required": "",
                "approved_egress_ip": "",
                "approved_ip_label": "",
                "approved_access_region": "",
                "access_profile_notes": "",
                "last_ip_check_at": "",
                "last_operator_update": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        channel.refresh_from_db()
        self.assertEqual(channel.last_operator_update, "")
        self.assertIsNone(channel.last_operator_update_at)

    def test_channel_update_redirects_back_to_saved_edit_form(self):
        admin = self.make_admin()
        creator = self.make_creator()
        channel = self.make_channel(creator=creator)

        self.client.login(username=admin.username, password=self.admin_password)

        response = self.client.post(
            reverse("channel-update", kwargs={"pk": channel.pk}),
            {
                "creator": creator.pk,
                "platform": channel.platform,
                "handle": channel.handle,
                "profile_url": "",
                "status": channel.status,
                "access_mode": channel.access_mode,
                "recovery_owner": channel.recovery_owner,
                "login_identifier": channel.login_identifier,
                "account_email": "",
                "account_phone_number": "",
                "credential_status": "",
                "access_notes": "",
                "last_access_check_at": "",
                "two_factor_enabled": "",
                "vpn_required": "",
                "approved_egress_ip": "",
                "approved_ip_label": "",
                "approved_access_region": "",
                "access_profile_notes": "",
                "last_ip_check_at": "",
                "last_operator_update": "Fresh update",
            },
        )

        self.assertRedirects(
            response,
            reverse("channel-update", kwargs={"pk": channel.pk}) + "?saved=1",
        )

    def test_operator_cannot_update_channel(self):
        creator = self.make_creator()
        channel = self.make_channel(creator=creator)
        operator_user, operator = self.make_operator_user()
        self.assign_operator(operator=operator, creator=creator)

        self.client.login(
            username=operator_user.username,
            password=self.operator_password,
        )
        response = self.client.get(reverse("channel-update", kwargs={"pk": channel.pk}))

        self.assertNotEqual(response.status_code, 200)

    def test_channel_detail_renders_existing_last_operator_update(self):
        admin = self.make_admin()
        creator = self.make_creator()
        channel = self.make_channel(
            creator=creator,
            last_operator_update="Need follow-up on login flow.",
            last_operator_update_at=timezone.now(),
        )

        self.client.login(username=admin.username, password=self.admin_password)
        response = self.client.get(reverse("channel-detail", kwargs={"pk": channel.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Need follow-up on login flow.")