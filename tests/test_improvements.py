"""
Tests for recent improvements: CalcManager, i18n coverage, activity_log.
"""

import pytest


class TestSafeCalculator:
    """Test the recursive descent arithmetic parser in CalcManager."""

    @pytest.fixture
    def calc(self):
        """Import CalcManager — works on any Python without PyQt5."""
        from core.calc_manager import CalcManager
        return CalcManager

    def test_addition(self, calc):
        assert calc.evaluate("2 + 3") == 5.0

    def test_subtraction(self, calc):
        assert calc.evaluate("10 - 4") == 6.0

    def test_multiplication(self, calc):
        assert calc.evaluate("3 * 7") == 21.0

    def test_division(self, calc):
        assert calc.evaluate("15 / 3") == 5.0

    def test_modulo(self, calc):
        assert calc.evaluate("10 % 3") == 1.0

    def test_parentheses(self, calc):
        assert calc.evaluate("(2 + 3) * 4") == 20.0

    def test_complex(self, calc):
        assert calc.evaluate("2 + 3 * 4 - 6 / 2") == 11.0

    def test_negative(self, calc):
        assert calc.evaluate("-5 + 3") == -2.0

    def test_decimal(self, calc):
        assert calc.evaluate("3.5 * 2") == 7.0

    def test_nested_parens(self, calc):
        assert calc.evaluate("((2 + 3) * 2)") == 10.0

    def test_invalid_chars(self, calc):
        with pytest.raises(Exception):
            calc.evaluate("2 + abc")

    def test_unmatched_parens(self, calc):
        with pytest.raises(Exception):
            calc.evaluate("(2 + 3")


class TestI18nCoverage:
    """Verify all i18n keys defined in both RU and EN."""

    def test_all_keys_in_both_langs(self):
        from i18n import TRANSLATIONS
        ru_keys = set(TRANSLATIONS["ru"].keys())
        en_keys = set(TRANSLATIONS["en"].keys())
        missing_in_en = ru_keys - en_keys
        missing_in_ru = en_keys - ru_keys
        assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"
        assert not missing_in_ru, f"Keys missing in RU: {missing_in_ru}"


class TestActivityLog:
    """Test the activity log improvements."""

    def test_log_with_db_failure(self, monkeypatch):
        """Logging should never crash even if the database is broken."""
        from core.activity_log import log, EVENT_CONVERT, STATUS_OK
        monkeypatch.setattr(
            "core.activity_log._conn",
            lambda: (_ for _ in ()).throw(Exception("DB fail"))
        )
        log(EVENT_CONVERT, STATUS_OK, "test")  # should not raise
