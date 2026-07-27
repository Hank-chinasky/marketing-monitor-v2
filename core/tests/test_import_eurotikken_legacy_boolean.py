from django.core.management.base import CommandError
from django.test import SimpleTestCase

from core.management.commands.import_eurotikken_operator_context import (
    _normalize_legacy_boolean,
)


class EurotikkenLegacyBooleanTests(SimpleTestCase):
    def test_accepts_booleans_and_exact_legacy_values(self):
        cases = (
            (True, True),
            (False, False),
            ("Y", True),
            ("N", False),
        )

        for raw_value, expected in cases:
            with self.subTest(raw_value=raw_value):
                self.assertIs(
                    _normalize_legacy_boolean(
                        raw_value,
                        field_name="profile_media[0].active",
                    ),
                    expected,
                )

    def test_rejects_ambiguous_values(self):
        invalid_values = (
            "y",
            "n",
            "yes",
            "no",
            "1",
            "0",
            1,
            0,
            None,
            "",
        )

        for raw_value in invalid_values:
            with self.subTest(raw_value=raw_value):
                with self.assertRaises(CommandError):
                    _normalize_legacy_boolean(
                        raw_value,
                        field_name="profile_media[0].active",
                    )
