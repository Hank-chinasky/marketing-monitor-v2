import json
import os
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from core.services.buddy_reply import (
    build_operator_reply_draft,
)
from core.services.buddy_venice import (
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    BUDDY_RESPONSE_SCHEMA,
    VeniceBuddyProvider,
    VeniceConfigurationError,
    VeniceProviderError,
    _NoRedirectHandler,
    _read_limited_response,
    build_venice_provider_from_environment,
)


def message(direction, body):
    return SimpleNamespace(
        direction=direction,
        body=body,
    )


def successful_provider_content(**overrides):
    content = {
        "draft_text": (
            "Dat klinkt alsof je nog aan ons gesprek dacht. "
            "Wat bleef je het meeste bij?"
        ),
        "language": "nl",
        "why_this_reply": (
            "Het concept pakt de bestaande open loop op."
        ),
        "open_loops_to_watch": [
            "Vraag wat hem is bijgebleven.",
        ],
        "do_not_do_warnings": [
            "Niet generiek openen.",
        ],
        "commercial_signal": "medium",
        "confidence": 0.84,
        "refusal_status": "none",
    }
    content.update(overrides)
    return content


def venice_response_bytes(content):
    return json.dumps(
        {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(content),
                    },
                    "finish_reason": "stop",
                }
            ],
        }
    ).encode("utf-8")


class CapturingTransport:
    def __init__(
        self,
        response_bytes=None,
        exception=None,
    ):
        self.response_bytes = (
            response_bytes
            if response_bytes is not None
            else venice_response_bytes(
                successful_provider_content()
            )
        )
        self.exception = exception
        self.calls = []

    def __call__(
        self,
        *,
        url,
        headers,
        body,
        timeout_seconds,
        max_response_bytes,
    ):
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "body": body,
                "timeout_seconds": timeout_seconds,
                "max_response_bytes": (
                    max_response_bytes
                ),
            }
        )

        if self.exception:
            raise self.exception

        return self.response_bytes


class FakeResponse:
    def __init__(
        self,
        body,
        *,
        content_type="application/json",
        content_length=None,
    ):
        self._body = BytesIO(body)
        self.headers = {
            "Content-Type": content_type,
        }

        if content_length is not None:
            self.headers["Content-Length"] = str(
                content_length
            )

    def read(self, size=-1):
        return self._body.read(size)


class VeniceAdapterV1Tests(SimpleTestCase):
    def test_environment_factory_requires_api_key(self):
        with patch.dict(
            os.environ,
            {
                "VENICE_API_KEY": "",
                "VENICE_MODEL": "test-model",
            },
            clear=False,
        ):
            with self.assertRaises(
                VeniceConfigurationError
            ):
                build_venice_provider_from_environment()

    def test_environment_factory_requires_model(self):
        with patch.dict(
            os.environ,
            {
                "VENICE_API_KEY": "secret-test-key",
                "VENICE_MODEL": "",
            },
            clear=False,
        ):
            with self.assertRaises(
                VeniceConfigurationError
            ):
                build_venice_provider_from_environment()

    def test_environment_factory_uses_safe_defaults(self):
        transport = CapturingTransport()

        with patch.dict(
            os.environ,
            {
                "VENICE_API_KEY": "secret-test-key",
                "VENICE_MODEL": "test-model",
                "VENICE_API_BASE": "",
                "VENICE_TIMEOUT_SECONDS": "",
                "VENICE_MAX_RESPONSE_BYTES": "",
            },
            clear=False,
        ):
            # Een lege expliciete base is ongeldig.
            with self.assertRaises(
                VeniceConfigurationError
            ):
                build_venice_provider_from_environment(
                    transport=transport,
                )

        with patch.dict(
            os.environ,
            {
                "VENICE_API_KEY": "secret-test-key",
                "VENICE_MODEL": "test-model",
            },
            clear=True,
        ):
            provider = (
                build_venice_provider_from_environment(
                    transport=transport,
                )
            )

        self.assertEqual(
            provider.timeout_seconds,
            DEFAULT_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            provider.max_response_bytes,
            DEFAULT_MAX_RESPONSE_BYTES,
        )

    def test_non_venice_host_is_rejected(self):
        with patch.dict(
            os.environ,
            {
                "VENICE_API_KEY": "secret-test-key",
                "VENICE_MODEL": "test-model",
                "VENICE_API_BASE": (
                    "https://example.com/api/v1"
                ),
            },
            clear=True,
        ):
            with self.assertRaises(
                VeniceConfigurationError
            ):
                build_venice_provider_from_environment()

    def test_insecure_http_base_is_rejected(self):
        with patch.dict(
            os.environ,
            {
                "VENICE_API_KEY": "secret-test-key",
                "VENICE_MODEL": "test-model",
                "VENICE_API_BASE": (
                    "http://api.venice.ai/api/v1"
                ),
            },
            clear=True,
        ):
            with self.assertRaises(
                VeniceConfigurationError
            ):
                build_venice_provider_from_environment()

    def test_direct_provider_revalidates_api_base(self):
        transport = CapturingTransport()

        with self.assertRaises(
            VeniceConfigurationError
        ):
            VeniceBuddyProvider(
                api_key="secret-test-key",
                model="test-model",
                api_base=(
                    "https://example.com/api/v1"
                ),
                transport=transport,
            )

        self.assertEqual(transport.calls, [])

    def test_direct_provider_rejects_unbounded_configuration(self):
        invalid_overrides = (
            {
                "api_key": "",
            },
            {
                "model": "",
            },
            {
                "timeout_seconds": 0,
            },
            {
                "timeout_seconds": 60.1,
            },
            {
                "max_response_bytes": 4_095,
            },
            {
                "max_response_bytes": 1_048_577,
            },
            {
                "transport": object(),
            },
        )

        for overrides in invalid_overrides:
            arguments = {
                "api_key": "secret-test-key",
                "model": "test-model",
                "transport": CapturingTransport(),
            }
            arguments.update(overrides)

            with self.subTest(overrides=overrides):
                with self.assertRaises(
                    VeniceConfigurationError
                ):
                    VeniceBuddyProvider(
                        **arguments
                    )

    def test_provider_repr_does_not_expose_api_key(self):
        provider = VeniceBuddyProvider(
            api_key="secret-test-key",
            model="test-model",
            transport=CapturingTransport(),
        )

        self.assertNotIn(
            "secret-test-key",
            repr(provider),
        )

    def test_request_is_bounded_and_structured(self):
        transport = CapturingTransport()
        provider = VeniceBuddyProvider(
            api_key="secret-test-key",
            model="test-model",
            transport=transport,
        )

        result = provider.generate_reply(
            context_packet={
                "schema_version": "buddy-context-v1",
                "latest_inbound_text": (
                    "Ik dacht vandaag weer aan je."
                ),
            }
        )

        self.assertEqual(
            result["refusal_status"],
            "none",
        )
        self.assertEqual(len(transport.calls), 1)

        call = transport.calls[0]
        request_payload = json.loads(
            call["body"].decode("utf-8")
        )

        self.assertEqual(
            call["url"],
            (
                "https://api.venice.ai/api/v1"
                "/chat/completions"
            ),
        )
        self.assertEqual(
            call["headers"]["Authorization"],
            "Bearer secret-test-key",
        )
        self.assertEqual(
            call["timeout_seconds"],
            DEFAULT_TIMEOUT_SECONDS,
        )
        self.assertEqual(
            call["max_response_bytes"],
            DEFAULT_MAX_RESPONSE_BYTES,
        )

        self.assertFalse(request_payload["stream"])
        self.assertFalse(request_payload["store"])
        self.assertFalse(
            request_payload["parallel_tool_calls"]
        )
        self.assertNotIn("tools", request_payload)

        self.assertEqual(
            request_payload["response_format"]["type"],
            "json_schema",
        )
        self.assertTrue(
            request_payload["response_format"][
                "json_schema"
            ]["strict"]
        )
        self.assertEqual(
            request_payload["response_format"][
                "json_schema"
            ]["schema"],
            BUDDY_RESPONSE_SCHEMA,
        )

        venice_parameters = request_payload[
            "venice_parameters"
        ]
        self.assertFalse(
            venice_parameters[
                "include_venice_system_prompt"
            ]
        )
        self.assertEqual(
            venice_parameters["enable_web_search"],
            "off",
        )
        self.assertFalse(
            venice_parameters[
                "enable_web_scraping"
            ]
        )
        self.assertFalse(
            venice_parameters[
                "enable_web_citations"
            ]
        )
        self.assertFalse(
            venice_parameters["enable_x_search"]
        )

    def test_outer_invalid_json_is_rejected(self):
        provider = VeniceBuddyProvider(
            api_key="secret-test-key",
            model="test-model",
            transport=CapturingTransport(
                response_bytes=b"not-json",
            ),
        )

        with self.assertRaises(VeniceProviderError):
            provider.generate_reply(
                context_packet={
                    "schema_version": (
                        "buddy-context-v1"
                    ),
                }
            )

    def test_invalid_structured_content_is_rejected(self):
        response_bytes = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "not-json",
                        }
                    }
                ]
            }
        ).encode("utf-8")

        provider = VeniceBuddyProvider(
            api_key="secret-test-key",
            model="test-model",
            transport=CapturingTransport(
                response_bytes=response_bytes,
            ),
        )

        with self.assertRaises(VeniceProviderError):
            provider.generate_reply(
                context_packet={
                    "schema_version": (
                        "buddy-context-v1"
                    ),
                }
            )

    def test_missing_choice_is_rejected(self):
        provider = VeniceBuddyProvider(
            api_key="secret-test-key",
            model="test-model",
            transport=CapturingTransport(
                response_bytes=json.dumps(
                    {
                        "choices": [],
                    }
                ).encode("utf-8"),
            ),
        )

        with self.assertRaises(VeniceProviderError):
            provider.generate_reply(
                context_packet={
                    "schema_version": (
                        "buddy-context-v1"
                    ),
                }
            )

    def test_transport_timeout_is_safely_wrapped(self):
        provider = VeniceBuddyProvider(
            api_key="secret-test-key",
            model="test-model",
            transport=CapturingTransport(
                exception=TimeoutError(
                    "secret-test-key"
                ),
            ),
        )

        with self.assertRaises(
            VeniceProviderError
        ) as captured:
            provider.generate_reply(
                context_packet={
                    "schema_version": (
                        "buddy-context-v1"
                    ),
                }
            )

        self.assertNotIn(
            "secret-test-key",
            str(captured.exception),
        )

    def test_declared_oversized_response_is_rejected(self):
        response = FakeResponse(
            b"{}",
            content_length=101,
        )

        with self.assertRaises(VeniceProviderError):
            _read_limited_response(
                response,
                max_response_bytes=100,
            )

    def test_actual_oversized_response_is_rejected(self):
        response = FakeResponse(
            b"x" * 101,
        )

        with self.assertRaises(VeniceProviderError):
            _read_limited_response(
                response,
                max_response_bytes=100,
            )

    def test_non_json_content_type_is_rejected(self):
        response = FakeResponse(
            b"{}",
            content_type="text/html",
        )

        with self.assertRaises(VeniceProviderError):
            _read_limited_response(
                response,
                max_response_bytes=100,
            )

    def test_redirect_handler_does_not_follow_redirects(self):
        handler = _NoRedirectHandler()

        result = handler.redirect_request(
            request=None,
            file_pointer=None,
            code=302,
            message="Found",
            headers={},
            new_url=(
                "https://example.com/redirect"
            ),
        )

        self.assertIsNone(result)

    def test_valid_adapter_output_passes_reply_validator(self):
        provider = VeniceBuddyProvider(
            api_key="secret-test-key",
            model="test-model",
            transport=CapturingTransport(),
        )

        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message(
                    "inbound",
                    "Hoi, ik dacht vandaag weer aan je.",
                ),
            ],
            provider=provider,
        )

        self.assertEqual(result["status"], "ready")
        self.assertIn(
            "Wat bleef je het meeste bij?",
            result["reply_text"],
        )
        self.assertEqual(
            result["source"],
            "provider:VeniceBuddyProvider",
        )
        self.assertTrue(
            result["requires_human_review"]
        )

    def test_invalid_adapter_output_becomes_provider_error(self):
        invalid_output = successful_provider_content(
            confidence=2.0,
        )
        provider = VeniceBuddyProvider(
            api_key="secret-test-key",
            model="test-model",
            transport=CapturingTransport(
                response_bytes=venice_response_bytes(
                    invalid_output
                ),
            ),
        )

        result = build_operator_reply_draft(
            selected_thread=object(),
            conversation_messages=[
                message(
                    "inbound",
                    "Hoi, kun je mij helpen?",
                ),
            ],
            provider=provider,
        )

        self.assertEqual(
            result["status"],
            "provider_error",
        )
        self.assertEqual(result["reply_text"], "")
