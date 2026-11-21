"""
Проверка обновлений AUTOMAT через GitHub Releases API.

Поток (в стиле Telegram Desktop):
1. Фоновая проверка `fetch_latest()` — страница Настроек, Ctrl+U,
   автопроверка при старте.
2. Если релиз новее — диалог с changelog (body релиза), кнопками
   «Скачать и установить» / «Позже» / «Пропустить версию».
3. Для собранного .exe скачивается `AUTOMAT-Setup-*.exe` из ассетов,
   запускается инсталлятор, приложение закрывается.
4. В dev-режиме (запуск из исходников) самообновление невозможно —
   открывается страница релиза в браузере.

Сеть только здесь; UI (app.py) вызывает эти функции из Worker'а.
"""

import logging
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

LOG = logging.getLogger("automat.updater")

GITHUB_OWNER = "TheOpenDevTeam"
GITHUB_REPO = "automat"
API_LATEST_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
RELEASES_PAGE_URL = (
    f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
)

INSTALLER_PREFIX = "AUTOMAT-Setup-"
INSTALLER_SUFFIX = ".exe"

AUTO_CHECK_INTERVAL_HOURS = 24


def version_tuple(v: str) -> tuple:
    """'v1.0.10' -> (1, 0, 10): сравнение численно, а не лексически."""
    parts = []
    for chunk in str(v).lstrip("vV").split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def is_newer(latest: str, current: str) -> bool:
    """True, если релиз на GitHub новее установленной версии."""
    try:
        return version_tuple(latest) > version_tuple(current)
    except Exception:
        return False


def normalize_tag(tag: str) -> str:
    return str(tag or "").strip().lstrip("vV")


def is_frozen() -> bool:
    """True для собранного PyInstaller .exe, False при запуске из исходников."""
    return bool(getattr(sys, "frozen", False))


def fetch_latest(proxies=None, timeout: int = 10) -> dict:
    """Запросить latest-релиз. Возвращает dict; при ошибке {'ok': False}.

    Не бросает исключений — фоновая задача не должна падать.
    """
    try:
        import requests
    except ImportError:
        return {"ok": False, "error": "no_requests"}
    try:
        r = requests.get(API_LATEST_URL, timeout=timeout, proxies=proxies)
        if r.status_code == 404:
            return {"ok": False, "error": "no_releases"}
        if r.status_code != 200:
            return {"ok": False, "error": f"http_{r.status_code}"}
        data = r.json()
    except Exception as exc:
        LOG.debug("update check failed: %s", exc)
        return {"ok": False, "error": "network"}

    tag = str(data.get("tag_name", "")).strip()
    if not tag:
        return {"ok": False, "error": "bad_response"}
    assets = data.get("assets") or []
    return {
        "ok": True,
        "version": normalize_tag(tag),
        "tag": tag,
        "url": data.get("html_url") or RELEASES_PAGE_URL,
        "notes": (data.get("body") or "").strip(),
        "published_at": data.get("published_at") or "",
        "assets": [
            {
                "name": a.get("name", ""),
                "url": a.get("browser_download_url", ""),
                "size": a.get("size", 0),
            }
            for a in assets
            if a.get("browser_download_url")
        ],
    }


def pick_installer_asset(release: dict):
    """Выбрать инсталлятор Windows из ассетов релиза (или None)."""
    for a in release.get("assets", []):
        name = a.get("name", "")
        if name.startswith(INSTALLER_PREFIX) and name.endswith(INSTALLER_SUFFIX):
            return a
    # Fallback: любой .exe, чтобы не молчать, если имя поменялось.
    for a in release.get("assets", []):
        if a.get("name", "").endswith(".exe"):
            return a
    return None


def download_asset(url: str, dest: Path, proxies=None, timeout: int = 30,
                   progress_cb=None, is_cancelled=None) -> Path:
    """Скачать файл потоково. progress_cb(downloaded, total)."""
    import requests

    dest = Path(dest)
    with requests.get(url, timeout=timeout, proxies=proxies, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if is_cancelled is not None and is_cancelled():
                    raise CancelledError()
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb is not None:
                    try:
                        progress_cb(downloaded, total)
                    except Exception:
                        pass
    return dest


class CancelledError(Exception):
    pass


def download_dir() -> Path:
    d = Path(tempfile.gettempdir()) / "AutomatUpdate"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------------------------
# Настройки автообновлений (хранятся в settings.json -> "updates")
# ------------------------------------------------------------------

DEFAULTS = {
    "auto_check": True,
    "last_check": "",
    "skipped_version": "",
}


def get_update_settings(settings_data: dict) -> dict:
    """Слить дефолты с сохранёнными (не мутирует вход)."""
    merged = dict(DEFAULTS)
    saved = (settings_data or {}).get("updates")
    if isinstance(saved, dict):
        for k in DEFAULTS:
            if k in saved:
                merged[k] = saved[k]
    return merged


def should_auto_check(settings_data: dict, now: datetime = None) -> bool:
    """Нужна ли тихая проверка при старте: включена + прошли сутки."""
    cfg = get_update_settings(settings_data)
    if not cfg.get("auto_check"):
        return False
    last = str(cfg.get("last_check") or "")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        now = now or datetime.now(timezone.utc)
        return (now - last_dt).total_seconds() >= AUTO_CHECK_INTERVAL_HOURS * 3600
    except Exception:
        return True


def mark_checked(settings_data: dict) -> None:
    settings_data["updates"] = {
        **get_update_settings(settings_data),
        "last_check": datetime.now(timezone.utc).isoformat(),
    }


def is_skipped(settings_data: dict, version: str) -> bool:
    cfg = get_update_settings(settings_data)
    return bool(version) and cfg.get("skipped_version") == version


# ------------------------------------------------------------------
# Онбординг: флаг «обучение уже показывали»
# ------------------------------------------------------------------

def onboarding_done(settings_data: dict) -> bool:
    return bool((settings_data or {}).get("onboarding_done", False))


def mark_onboarding_done(settings_data: dict) -> None:
    settings_data["onboarding_done"] = True


def launch_installer(path: Path) -> bool:
    """Запустить скачанный инсталлятор и вернуть True (caller закроет app)."""
    try:
        if os.name == "nt":
            os.startfile(str(path))  # noqa: S606 — путь из нашего temp-каталога
        else:
            import subprocess
            subprocess.Popen([str(path)])
        return True
    except Exception as exc:
        LOG.error("cannot launch installer %s: %s", path, exc)
        return False
