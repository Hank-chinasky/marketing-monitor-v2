from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from core.models import Creator, CreatorChannel

User = get_user_model()


class BaseDataMixin:
    admin_password = "testpass123"

    def make_admin(self, username="admin"):
        return User.objects.create_user(
            username=username,
            password=self.admin_password,
            is_staff=True,
            is_superuser=True,
        )

    def make_creator(
        self,
        display_name="Creator A",
        status="active",
        consent_status="active",
    ):
        return Creator.objects.create(
            display_name=display_name,
            status=status,
            consent_status=consent_status,
        )

    def make_channel(
        self,
        creator,
        handle="creator_a",
        platform="instagram",
        status="active",
        access_mode="operator_direct",
        recovery_owner="agency",
        login_identifier="login_creator_a",
        account_email="creator@example.com",
        account_phone_number="",
        credential_status="known",
        two_factor_enabled=True,
        vpn_required=False,
        approved_ip_label="",
        approved_egress_ip="",
        last_operator_update="Healthy update",
        profile_url="",
    ):
        return CreatorChannel.objects.create(
            creator=creator,
            platform=platform,
            handle=handle,
            profile_url=profile_url,
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
        )

    def build_channel_update_payload(
        self,
        channel,
        next_url="",
        last_operator_update=None,
    ):
        payload = {
            "creator": channel.creator.pk,
            "platform": channel.platform,
            "handle": channel.handle,
            "profile_url": channel.profile_url,
            "status": channel.status,
            "access_mode": channel.access_mode,
            "recovery_owner": channel.recovery_owner,
            "login_identifier": channel.login_identifier,
            "account_email": channel.account_email,
            "account_phone_number": channel.account_phone_number,
            "credential_status": channel.credential_status,
            "access_notes": channel.access_notes,
            "last_access_check_at": "",
            "two_factor_enabled": "on" if channel.two_factor_enabled else "",
            "vpn_required": "on" if channel.vpn_required else "",
            "approved_egress_ip": channel.approved_egress_ip,
            "approved_ip_label": channel.approved_ip_label,
            "approved_access_region": channel.approved_access_region,
            "access_profile_notes": channel.access_profile_notes,
            "last_ip_check_at": "",
            "last_operator_update": (
                channel.last_operator_update
                if last_operator_update is None
                else last_operator_update
            ),
        }

        if next_url:
            payload["next"] = next_url

        return payload


class ChannelQueuePresetTests(BaseDataMixin, TestCase):
    def setUp(self):
        self.admin = self.make_admin()
        self.creator = self.make_creator()
        self.client.login(username=self.admin.username, password=self.admin_password)

    def test_needs_reset_preset_shows_only_reset_channels(self):
        reset_channel = self.make_channel(
            creator=self.creator,
            handle="reset_channel",
            credential_status="needs_reset",
        )
        healthy_channel = self.make_channel(
            creator=self.creator,
            handle="healthy_channel",
        )

        response = self.client.get(
            reverse("channel-list"),
            {"preset": "needs_reset"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reset_channel.handle)
        self.assertNotContains(response, healthy_channel.handle)

    def test_no_2fa_preset_shows_only_channels_without_2fa(self):
        no_2fa_channel = self.make_channel(
            creator=self.creator,
            handle="no_2fa_channel",
            two_factor_enabled=False,
        )
        healthy_channel = self.make_channel(
            creator=self.creator,
            handle="healthy_2fa_channel",
            two_factor_enabled=True,
        )

        response = self.client.get(
            reverse("channel-list"),
            {"preset": "no_2fa"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, no_2fa_channel.handle)
        self.assertNotContains(response, healthy_channel.handle)

    def test_vpn_gap_preset_shows_only_channels_with_policy_gap(self):
        vpn_gap_channel = self.make_channel(
            creator=self.creator,
            handle="vpn_gap_channel",
            vpn_required=True,
            approved_ip_label="",
            approved_egress_ip="",
        )
        healthy_vpn_channel = self.make_channel(
            creator=self.creator,
            handle="vpn_ok_channel",
            vpn_required=True,
            approved_ip_label="ams-vpn-1",
        )

        response = self.client.get(
            reverse("channel-list"),
            {"preset": "vpn_gap"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, vpn_gap_channel.handle)
        self.assertNotContains(response, healthy_vpn_channel.handle)

    def test_no_identifier_preset_shows_only_channels_without_identifiers(self):
        missing_identifier_channel = self.make_channel(
            creator=self.creator,
            handle="missing_identifier_channel",
            login_identifier="",
            account_email="",
            account_phone_number="",
        )
        healthy_channel = self.make_channel(
            creator=self.creator,
            handle="has_identifier_channel",
            login_identifier="has_login",
        )

        response = self.client.get(
            reverse("channel-list"),
            {"preset": "no_identifier"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, missing_identifier_channel.handle)
        self.assertNotContains(response, healthy_channel.handle)

    def test_no_update_preset_shows_only_channels_without_last_update(self):
        missing_update_channel = self.make_channel(
            creator=self.creator,
            handle="missing_update_channel",
            last_operator_update="",
        )
        healthy_channel = self.make_channel(
            creator=self.creator,
            handle="has_update_channel",
            last_operator_update="Already updated",
        )

        response = self.client.get(
            reverse("channel-list"),
            {"preset": "no_update"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, missing_update_channel.handle)
        self.assertNotContains(response, healthy_channel.handle)


class ChannelQueueNavigationTests(BaseDataMixin, TestCase):
    def setUp(self):
        self.admin = self.make_admin()
        self.creator = self.make_creator()
        self.channel = self.make_channel(
            creator=self.creator,
            handle="queue_channel",
            last_operator_update="Needs follow-up",
        )
        self.client.login(username=self.admin.username, password=self.admin_password)

    def test_channel_detail_from_queue_shows_back_link_to_same_queue(self):
        queue_url = reverse("channel-list") + "?preset=issues&q=queue"

        response = self.client.get(
            reverse("channel-detail", kwargs={"pk": self.channel.pk}),
            {"next": queue_url},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Terug naar queue")
        self.assertContains(response, escape(queue_url))

    def test_channel_update_from_queue_redirects_back_to_same_queue_with_updated_flag(self):
        queue_url = reverse("channel-list") + "?preset=no_update&q=queue"

        response = self.client.post(
            reverse("channel-update", kwargs={"pk": self.channel.pk}),
            self.build_channel_update_payload(
                self.channel,
                next_url=queue_url,
                last_operator_update="Queue updated successfully",
            ),
        )

        self.assertRedirects(
            response,
            queue_url + "&updated=1",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("updated=1", response.url)
  
        self.channel.refresh_from_db()
        sself.assertEqual(
    self.channel.last_operator_update,
    "Needs follow-up",
)