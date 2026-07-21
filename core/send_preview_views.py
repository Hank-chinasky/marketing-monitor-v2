import json
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.cache import patch_cache_control
from django.views import View

from core.services.contact_data_sanitizer import (
    sanitize_contact_data,
)
from core.services.demo_access import is_demo_viewer


MAX_SEND_PREVIEW_LENGTH = 10_000


def _preview_json(
    payload: dict[str, Any],
    *,
    status: int = 200,
) -> JsonResponse:
    response = JsonResponse(payload, status=status)
    patch_cache_control(
        response,
        no_store=True,
        private=True,
    )
    return response


class SanitizedSendPreviewView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if is_demo_viewer(request.user):
            return _preview_json(
                {
                    "error": "read_only",
                    "send_available": False,
                },
                status=403,
            )

        if request.content_type != "application/json":
            return _preview_json(
                {
                    "error": "invalid_content_type",
                    "send_available": False,
                },
                status=415,
            )

        try:
            payload = json.loads(
                request.body.decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _preview_json(
                {
                    "error": "invalid_json",
                    "send_available": False,
                },
                status=400,
            )

        if not isinstance(payload, dict):
            return _preview_json(
                {
                    "error": "invalid_payload",
                    "send_available": False,
                },
                status=400,
            )

        message = payload.get("message")

        if not isinstance(message, str):
            return _preview_json(
                {
                    "error": "message_required",
                    "send_available": False,
                },
                status=400,
            )

        if not message.strip():
            return _preview_json(
                {
                    "error": "message_empty",
                    "send_available": False,
                },
                status=400,
            )

        if len(message) > MAX_SEND_PREVIEW_LENGTH:
            return _preview_json(
                {
                    "error": "message_too_long",
                    "send_available": False,
                },
                status=413,
            )

        result = sanitize_contact_data(message)

        return _preview_json(
            {
                "preview_text": result.sanitized_text,
                "changed": result.changed,
                "blocked": result.changed,
                "match_types": list(result.match_types),
                "status": (
                    "contact_data_blocked"
                    if result.changed
                    else "ready_for_review"
                ),
                "send_available": False,
            }
        )
