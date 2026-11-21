"""Тесты ядра автообновлений и онбординга — чистая логика, без сети и Qt."""

from datetime import datetime, timedelta, timezone

from automat.core import updater


def test_version_tuple_numeric_not_lexical():
    assert updater.version_tuple("1.0.10") > updater.version_tuple("1.0.9")
    assert updater.version_tuple("v2.0") > updater.version_tuple("1.99.99")


def test_is_newer():
    assert updater.is_newer("1.0.1", "1.0.0")
    assert updater.is_newer("v1.0.1", "1.0.0")
    assert not updater.is_newer("1.0.0", "1.0.0")
    assert not updater.is_newer("0.9.9", "1.0.0")


def test_pick_installer_asset():
    release = {"assets": [
        {"name": "checksums.txt", "url": "http://x/c", "size": 10},
        {"name": "AUTOMAT-Setup-1.0.1.exe", "url": "http://x/a", "size": 1},
    ]}
    asset = updater.pick_installer_asset(release)
    assert asset is not None and asset["url"] == "http://x/a"
    assert updater.pick_installer_asset({"assets": []}) is None


def test_update_settings_defaults_and_merge():
    cfg = updater.get_update_settings({})
    assert cfg["auto_check"] is True
    assert cfg["skipped_version"] == ""
    cfg2 = updater.get_update_settings({"updates": {"auto_check": False}})
    assert cfg2["auto_check"] is False
    assert cfg2["last_check"] == ""


def test_should_auto_check_first_run_and_interval():
    assert updater.should_auto_check({}) is True
    assert updater.should_auto_check({"updates": {"auto_check": False}}) is False
    recent = datetime.now(timezone.utc).isoformat()
    assert updater.should_auto_check(
        {"updates": {"auto_check": True, "last_check": recent}}) is False
    old = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    assert updater.should_auto_check(
        {"updates": {"auto_check": True, "last_check": old}}) is True


def test_skip_and_mark_checked():
    s = {}
    updater.mark_checked(s)
    assert s["updates"]["last_check"]
    assert not updater.is_skipped(s, "1.0.1")
    s["updates"]["skipped_version"] = "1.0.1"
    assert updater.is_skipped(s, "1.0.1")
    assert not updater.is_skipped(s, "1.0.2")


def test_onboarding_flag():
    s = {}
    assert not updater.onboarding_done(s)
    updater.mark_onboarding_done(s)
    assert updater.onboarding_done(s)


def test_fetch_latest_no_crash_without_requests(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "requests", None)
    # requests=None в sys.modules -> ImportError при import -> {'ok': False}
    data = updater.fetch_latest()
    assert data["ok"] is False


def test_i18n_has_update_and_onboard_keys():
    from automat.i18n import TRANSLATIONS
    keys = ["auto_update_auto", "auto_update_install", "auto_update_skip_version",
            "auto_update_open_page", "auto_update_dev_mode",
            "settings_show_onboarding", "onboard_title", "onboard_skip",
            "onboard_back", "onboard_next", "onboard_finish",
            "onboard_1_title", "onboard_1_text", "onboard_5_title", "onboard_5_text"]
    for lang in ("ru", "en"):
        for k in keys:
            assert k in TRANSLATIONS[lang], f"{lang}.{k} missing"
