"""
Comprehensive tests for AUTOMAT core modules:
- CalcManager (safe arithmetic parser)
- activity_log (SQLite logging)
- i18n (translation system)
- ThemeManager basics
"""

import pytest
import json
import os
import sys
from pathlib import Path


# ======================================================================
# CalcManager tests
# ======================================================================

class TestCalcManager:
    """Test the recursive descent arithmetic parser."""

    @pytest.fixture
    def calc(self):
        from automat.core.calc_manager import CalcManager
        return CalcManager

    def test_addition(self, calc):
        assert calc.evaluate("2+3") == 5.0

    def test_subtraction(self, calc):
        assert calc.evaluate("10-4") == 6.0

    def test_multiplication(self, calc):
        assert calc.evaluate("3*7") == 21.0

    def test_division(self, calc):
        assert calc.evaluate("15/3") == 5.0

    def test_modulo(self, calc):
        assert calc.evaluate("10%3") == 1.0

    def test_parentheses(self, calc):
        assert calc.evaluate("(2+3)*4") == 20.0

    def test_complex_expression(self, calc):
        assert calc.evaluate("2+3*4-6/2") == 11.0

    def test_negative_number(self, calc):
        assert calc.evaluate("-5+3") == -2.0

    def test_decimal(self, calc):
        assert calc.evaluate("3.5*2") == 7.0

    def test_nested_parens(self, calc):
        assert calc.evaluate("((2+3)*2)") == 10.0

    def test_whitespace_handling(self, calc):
        assert calc.evaluate("  2 + 3  ") == 5.0

    def test_invalid_chars(self, calc):
        with pytest.raises(Exception):
            calc.evaluate("2+abc")

    def test_unmatched_parens(self, calc):
        with pytest.raises(Exception):
            calc.evaluate("(2+3")

    def test_empty_expression(self, calc):
        with pytest.raises(Exception):
            calc.evaluate("")

    def test_is_valid(self, calc):
        assert calc.is_valid("2+3") is True
        assert calc.is_valid("abc") is False
        assert calc.is_valid("") is False


# ======================================================================
# activity_log tests
# ======================================================================

class TestActivityLog:
    """Test the SQLite activity logging system."""

    def test_log_with_db_failure(self, monkeypatch):
        """Log should not raise even if DB fails."""
        from automat.core.activity_log import log, EVENT_CONVERT, STATUS_OK
        monkeypatch.setattr(
            "automat.core.activity_log._conn",
            lambda: (_ for _ in ()).throw(Exception("DB fail"))
        )
        log(EVENT_CONVERT, STATUS_OK, "test")  # should not raise

    def test_get_success_rate_empty(self):
        """Success rate on empty DB should be 1.0."""
        from automat.core.activity_log import get_success_rate
        rate = get_success_rate()
        assert rate == 1.0

    def test_event_constants(self):
        """Verify event type constants are defined."""
        from automat.core import activity_log
        assert activity_log.EVENT_CONVERT == "convert"
        assert activity_log.EVENT_SEND == "send"
        assert activity_log.EVENT_HASH == "hash"
        assert activity_log.EVENT_SCHEDULE == "schedule"
        assert activity_log.EVENT_FILEOP == "fileop"
        assert activity_log.EVENT_CLEAN == "clean"
        assert activity_log.EVENT_DATAGEN == "datagen"
        assert activity_log.EVENT_TEXT == "text"

    def test_status_constants(self):
        """Verify status constants are defined."""
        from automat.core import activity_log
        assert activity_log.STATUS_OK == "ok"
        assert activity_log.STATUS_ERROR == "error"
        assert activity_log.STATUS_SKIP == "skip"


# ======================================================================
# i18n tests
# ======================================================================

class TestI18n:
    """Test the internationalization system."""

    def test_all_keys_in_both_langs(self):
        from automat.i18n import TRANSLATIONS
        ru_keys = set(TRANSLATIONS["ru"].keys())
        en_keys = set(TRANSLATIONS["en"].keys())
        missing_in_en = ru_keys - en_keys
        missing_in_ru = en_keys - ru_keys
        assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"
        assert not missing_in_ru, f"Keys missing in RU: {missing_in_ru}"

    def test_basic_translation(self):
        from automat.i18n import I18n
        i18n = I18n("ru")
        assert i18n.tr("app_title") == "AUTOMAT — Менеджер автоматизации задач"

    def test_english_translation(self):
        from automat.i18n import I18n
        i18n = I18n("en")
        assert i18n.tr("app_title") == "AUTOMAT — Task Automation Manager"

    def test_format_string(self):
        from automat.i18n import I18n
        i18n = I18n("ru")
        result = i18n.tr("app_subtitle", version="2.0")
        assert result == "v2.0"

    def test_fallback_to_ru(self):
        from automat.i18n import I18n
        i18n = I18n("de")  # unsupported language
        assert i18n.lang == "ru"

    def test_missing_key_returns_key(self):
        from automat.i18n import I18n
        i18n = I18n("ru")
        assert i18n.tr("nonexistent_key") == "nonexistent_key"

    def test_language_switch(self):
        from automat.i18n import I18n
        i18n = I18n("ru")
        assert i18n.tr("status_ready") == "Готов к работе"
        i18n.lang = "en"
        assert i18n.tr("status_ready") == "Ready"

    def test_invalid_language_set(self):
        from automat.i18n import I18n
        i18n = I18n("ru")
        i18n.lang = "xyz"
        assert i18n.lang == "ru"  # unchanged

    def test_sidebar_keys_exist(self):
        from automat.i18n import TRANSLATIONS
        for lang in ["ru", "en"]:
            assert "sidebar_tools" in TRANSLATIONS[lang]
            assert "sidebar_new" in TRANSLATIONS[lang]
            assert "sidebar_system" in TRANSLATIONS[lang]

    def test_page_keys_count(self):
        """Verify all 16 page keys exist in translations."""
        from automat.i18n import TRANSLATIONS
        page_keys = [
            "page_dash", "page_convert", "page_bulk", "page_telegram",
            "page_hash", "page_datagen", "page_cleandata", "page_fileops",
            "page_cron", "page_text", "page_ssh", "page_git",
            "page_api", "page_sysmon", "page_snippets", "page_settings",
        ]
        for lang in ["ru", "en"]:
            for key in page_keys:
                assert key in TRANSLATIONS[lang], f"Missing {key} in {lang}"


# ======================================================================
# ThemeManager tests
# ======================================================================

class TestThemeManager:
    """Test ThemeManager basics (without QApplication)."""

    @pytest.fixture(autouse=True)
    def _require_pyqt5(self):
        pytest.importorskip("PyQt5", reason="PyQt5 not installed")

    def test_default_theme(self, tmp_path):
        settings_file = str(tmp_path / "settings.json")
        settings = {"theme": "dark"}
        from automat.core.theme_manager import ThemeManager
        mgr = ThemeManager(settings, settings_file)
        assert mgr.current == "dark"
        assert mgr.is_dark is True

    def test_toggle(self, tmp_path):
        settings_file = str(tmp_path / "settings.json")
        settings = {"theme": "dark"}
        from automat.core.theme_manager import ThemeManager
        mgr = ThemeManager(settings, settings_file)
        new = mgr.toggle()
        assert new == "light"
        assert mgr.current == "light"
        assert mgr.is_dark is False

    def test_qss_loaded(self, tmp_path):
        settings_file = str(tmp_path / "settings.json")
        settings = {"theme": "dark"}
        from automat.core.theme_manager import ThemeManager
        mgr = ThemeManager(settings, settings_file)
        assert "dark" in mgr._qss_cache
        assert "light" in mgr._qss_cache
        assert len(mgr._qss_cache["dark"]) > 100
