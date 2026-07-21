from django.test import SimpleTestCase

from core.services.contact_data_sanitizer import (
    ContactDataSanitizationResult,
    sanitize_contact_data,
)


class ContactDataSanitizerV1Tests(SimpleTestCase):
    def test_replaces_recognizable_email_addresses(self):
        result = sanitize_contact_data(
            (
                "Mail jan@example.com of "
                "Support.Team+nl@example.co.uk."
            )
        )

        self.assertEqual(
            result.sanitized_text,
            "Mail ########## of ##########.",
        )
        self.assertTrue(result.changed)
        self.assertEqual(
            result.match_types,
            ("email",),
        )

    def test_replaces_common_phone_number_formats(self):
        result = sanitize_contact_data(
            (
                "Bel 0612345678, +31 6 12345678, "
                "020-123-4567 of 0032 (0) 478 12 34 56."
            )
        )

        self.assertEqual(
            result.sanitized_text.count("##########"),
            4,
        )
        self.assertNotIn("0612345678", result.sanitized_text)
        self.assertNotIn("+31 6 12345678", result.sanitized_text)
        self.assertNotIn("020-123-4567", result.sanitized_text)
        self.assertTrue(result.changed)
        self.assertEqual(
            result.match_types,
            ("phone",),
        )

    def test_preserves_separated_nine_digit_references(self):
        original = (
            "Referentie 123-456-789, "
            "dossier 123 456 789 en datum 2026-07-19."
        )

        result = sanitize_contact_data(original)

        self.assertEqual(result.sanitized_text, original)
        self.assertFalse(result.changed)
        self.assertEqual(result.match_types, ())

    def test_masks_ten_digit_phone_without_zero_prefix(self):
        result = sanitize_contact_data(
            "Bel 212-555-1234."
        )

        self.assertEqual(
            result.sanitized_text,
            "Bel ##########.",
        )
        self.assertTrue(result.changed)
        self.assertEqual(
            result.match_types,
            ("phone",),
        )

    def test_reports_both_match_types_without_original_values(self):
        email = "secret.person@example.com"
        phone = "+31 (0)6 1234 5678"

        result = sanitize_contact_data(
            f"Mail {email} of bel {phone}."
        )

        self.assertEqual(
            result.match_types,
            ("email", "phone"),
        )
        self.assertNotIn(email, result.sanitized_text)
        self.assertNotIn(phone, result.sanitized_text)
        self.assertNotIn(email, repr(result))
        self.assertNotIn(phone, repr(result))

    def test_preserves_dates_times_amounts_ages_and_normal_numbers(self):
        original = (
            "Afspraak 19-07-2026 om 20:30. "
            "Ik ben 42 jaar en het kost 25 euro. "
            "Ordernummer 123456789."
        )

        result = sanitize_contact_data(original)

        self.assertEqual(result.sanitized_text, original)
        self.assertFalse(result.changed)
        self.assertEqual(result.match_types, ())

    def test_unchanged_text_remains_byte_for_byte_equal(self):
        original = "Hoi! Dit is gewone tekst.\nTweede regel."

        result = sanitize_contact_data(original)

        self.assertEqual(result.sanitized_text, original)
        self.assertFalse(result.changed)

    def test_empty_and_none_values_are_safe(self):
        for value in ("", None):
            with self.subTest(value=value):
                result = sanitize_contact_data(value)

                self.assertEqual(
                    result,
                    ContactDataSanitizationResult(
                        sanitized_text="",
                        changed=False,
                        match_types=(),
                    ),
                )

    def test_custom_replacements_support_buddy_context(self):
        result = sanitize_contact_data(
            "Mail jan@example.com of bel 0612345678.",
            email_replacement="[email]",
            phone_replacement="[phone]",
        )

        self.assertEqual(
            result.sanitized_text,
            "Mail [email] of bel [phone].",
        )
        self.assertEqual(
            result.match_types,
            ("email", "phone"),
        )
