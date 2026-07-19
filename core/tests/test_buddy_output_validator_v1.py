from django.test import SimpleTestCase

from core.services.buddy_output import (
    MAX_DRAFT_TEXT_LENGTH,
    BuddyOutputValidationError,
    validate_buddy_output,
)


class BuddyOutputValidatorV1Tests(SimpleTestCase):
    def test_valid_full_output_is_normalized(self):
        result = validate_buddy_output(
            {
                "draft_text": "  Hoi, fijn dat je er weer bent.  ",
                "language": "nl",
                "why_this_reply": "  Sluit aan op de open loop.  ",
                "open_loops_to_watch": [
                    "  Vraag naar zijn werkdag.  ",
                    "Pak de eerdere belofte weer op.",
                ],
                "do_not_do_warnings": [
                    "Niet generiek openen.",
                ],
                "commercial_signal": "medium",
                "confidence": 0.82,
                "refusal_status": "none",
            }
        )

        self.assertEqual(
            result["draft_text"],
            "Hoi, fijn dat je er weer bent.",
        )
        self.assertEqual(result["language"], "nl")
        self.assertEqual(
            result["why_this_reply"],
            "Sluit aan op de open loop.",
        )
        self.assertEqual(
            result["open_loops_to_watch"][0],
            "Vraag naar zijn werkdag.",
        )
        self.assertEqual(result["commercial_signal"], "medium")
        self.assertEqual(result["confidence"], 0.82)
        self.assertEqual(result["refusal_status"], "none")

    def test_unknown_fields_are_discarded(self):
        result = validate_buddy_output(
            {
                "draft_text": "Geldig antwoord.",
                "unknown_debug_data": "mag niet door",
                "source": "provider-controlled-source",
            }
        )

        self.assertNotIn("unknown_debug_data", result)
        self.assertNotIn("source", result)

    def test_non_mapping_output_is_rejected(self):
        with self.assertRaises(BuddyOutputValidationError):
            validate_buddy_output("geen mapping")

    def test_missing_draft_text_is_rejected_for_normal_response(self):
        with self.assertRaises(BuddyOutputValidationError):
            validate_buddy_output(
                {
                    "language": "nl",
                    "refusal_status": "none",
                }
            )

    def test_non_string_draft_text_is_rejected(self):
        with self.assertRaises(BuddyOutputValidationError):
            validate_buddy_output(
                {
                    "draft_text": 123,
                }
            )

    def test_overlong_draft_text_is_rejected(self):
        with self.assertRaises(BuddyOutputValidationError):
            validate_buddy_output(
                {
                    "draft_text": "x" * (
                        MAX_DRAFT_TEXT_LENGTH + 1
                    ),
                }
            )

    def test_unsupported_language_is_rejected(self):
        with self.assertRaises(BuddyOutputValidationError):
            validate_buddy_output(
                {
                    "draft_text": "Geldig antwoord.",
                    "language": "fr",
                }
            )

    def test_confidence_outside_range_is_rejected(self):
        for confidence in (-0.01, 1.01):
            with self.subTest(confidence=confidence):
                with self.assertRaises(
                    BuddyOutputValidationError
                ):
                    validate_buddy_output(
                        {
                            "draft_text": "Geldig antwoord.",
                            "confidence": confidence,
                        }
                    )

    def test_boolean_confidence_is_rejected(self):
        with self.assertRaises(BuddyOutputValidationError):
            validate_buddy_output(
                {
                    "draft_text": "Geldig antwoord.",
                    "confidence": True,
                }
            )

    def test_list_fields_require_string_lists(self):
        invalid_values = [
            "geen lijst",
            ["goed", 123],
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(
                    BuddyOutputValidationError
                ):
                    validate_buddy_output(
                        {
                            "draft_text": "Geldig antwoord.",
                            "open_loops_to_watch": value,
                        }
                    )

    def test_list_fields_are_bounded_to_five_items(self):
        result = validate_buddy_output(
            {
                "draft_text": "Geldig antwoord.",
                "open_loops_to_watch": [
                    f"Open loop {number}"
                    for number in range(1, 8)
                ],
            }
        )

        self.assertEqual(
            result["open_loops_to_watch"],
            [
                "Open loop 1",
                "Open loop 2",
                "Open loop 3",
                "Open loop 4",
                "Open loop 5",
            ],
        )

    def test_refusal_is_explicit_and_contains_no_draft(self):
        result = validate_buddy_output(
            {
                "draft_text": "",
                "language": "nl",
                "why_this_reply": "Onvoldoende veilige context.",
                "confidence": 0.2,
                "refusal_status": "refused",
            }
        )

        self.assertEqual(result["refusal_status"], "refused")
        self.assertEqual(result["draft_text"], "")
        self.assertEqual(
            result["why_this_reply"],
            "Onvoldoende veilige context.",
        )

    def test_refusal_with_draft_text_is_rejected(self):
        with self.assertRaises(BuddyOutputValidationError):
            validate_buddy_output(
                {
                    "draft_text": "Toch een antwoord.",
                    "refusal_status": "refused",
                }
            )

    def test_unsupported_commercial_signal_is_rejected(self):
        with self.assertRaises(BuddyOutputValidationError):
            validate_buddy_output(
                {
                    "draft_text": "Geldig antwoord.",
                    "commercial_signal": "buy-now",
                }
            )
