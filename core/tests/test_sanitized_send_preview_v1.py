import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import (
    Client,
    TestCase,
)
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core.services.demo_access import (
    DEMO_VIEWER_GROUP_NAME,
)


class SanitizedSendPreviewV1Tests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.operator_user = user_model.objects.create_user(
            username="send-preview-operator",
            password="x",
            is_active=True,
        )
        self.demo_user = user_model.objects.create_user(
            username="send-preview-demo",
            password="x",
            is_active=True,
        )

        demo_group = Group.objects.create(
            name=DEMO_VIEWER_GROUP_NAME
        )
        self.demo_user.groups.add(demo_group)

        self.url = reverse("sanitized-send-preview")

    def _post(self, message):
        return self.client.post(
            self.url,
            data=json.dumps({"message": message}),
            content_type="application/json",
        )

    def test_masks_contact_data_without_returning_original_values(self):
        self.client.force_login(self.operator_user)

        email = "secret.person@example.com"
        phone = "+31 6 12345678"

        response = self._post(
            (
                f"Mail {email} of bel {phone}. "
                "Afspraak 19-07-2026."
            )
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(
            payload["preview_text"],
            (
                "Mail ########## of bel ##########. "
                "Afspraak 19-07-2026."
            ),
        )
        self.assertTrue(payload["changed"])
        self.assertTrue(payload["blocked"])
        self.assertEqual(
            payload["match_types"],
            ["email", "phone"],
        )
        self.assertFalse(payload["send_available"])
        self.assertNotIn(email, response.content.decode())
        self.assertNotIn(phone, response.content.decode())
        self.assertIn(
            "no-store",
            response.headers["Cache-Control"],
        )
        self.assertIn(
            "private",
            response.headers["Cache-Control"],
        )

    def test_returns_unchanged_preview_when_no_contact_data_exists(self):
        self.client.force_login(self.operator_user)

        message = (
            "Afspraak 19-07-2026 om 20:30. "
            "Ordernummer 123456789."
        )

        response = self._post(message)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "preview_text": message,
                "changed": False,
                "blocked": False,
                "match_types": [],
                "status": "ready_for_review",
                "send_available": False,
            },
        )

    def test_rejects_invalid_json(self):
        self.client.force_login(self.operator_user)

        response = self.client.post(
            self.url,
            data="{",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "invalid_json",
        )

    def test_rejects_empty_message(self):
        self.client.force_login(self.operator_user)

        response = self._post("   ")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "message_empty",
        )

    def test_rejects_oversized_message(self):
        self.client.force_login(self.operator_user)

        response = self._post("x" * 10_001)

        self.assertEqual(response.status_code, 413)
        self.assertEqual(
            response.json()["error"],
            "message_too_long",
        )

    def test_demo_viewer_is_blocked_before_preview_view(self):
        self.client.force_login(self.demo_user)

        response = self._post("Gewone previewtekst.")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            response.headers["Content-Type"].startswith(
                "text/html"
            )
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self._post("Gewone previewtekst.")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_get_is_not_allowed(self):
        self.client.force_login(self.operator_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_csrf_is_required_for_browser_post(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.operator_user)

        response = csrf_client.post(
            self.url,
            data=json.dumps(
                {"message": "Gewone previewtekst."}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_preview_request_performs_no_database_write(self):
        self.client.force_login(self.operator_user)

        with CaptureQueriesContext(connection) as queries:
            response = self._post(
                "Mail jan@example.com."
            )

        self.assertEqual(response.status_code, 200)

        write_prefixes = (
            "INSERT ",
            "UPDATE ",
            "DELETE ",
            "REPLACE ",
        )

        write_queries = [
            query["sql"]
            for query in queries.captured_queries
            if query["sql"].lstrip().upper().startswith(
                write_prefixes
            )
        ]

        self.assertEqual(write_queries, [])
