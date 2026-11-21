# AGENTS.md — AUTOMAT

PyQt5 desktop automation app (Python >=3.9). Package `automat/`, 22 tool pages in `automat/ui/pages/`, entry `automat/main.py`.

## Commands

- Install: `pip install -e .` (preferred; `requirements.txt` is only a mirror)
- Run: `python -m automat.main` (from repo root; `RUN_APP.bat` is stale — it `cd`s into `automat/`)
- Tests (always headless): `QT_QPA_PLATFORM=offscreen pytest tests/ -q`
- Single test: `QT_QPA_PLATFORM=offscreen pytest tests/test_<name>.py -q`
- Build exe (CI does this; repo root, not `automat/`): `pyinstaller --noconfirm --clean --onedir --windowed --name "AUTOMAT" --paths . automat/main.py`, then Inno Setup `installer/automat.iss`. No `--add-data` — icons/QSS live in Python modules.
- No lint / typecheck / formatter config in repo. CI (`test.yml`) only runs pytest on Python 3.11 + Qt runtime libs (`libgl1 libegl1 libxkbcommon0 libdbus-1-3` on Ubuntu).

## Test isolation (do not break)

- `tests/conftest.py` sets `QT_QPA_PLATFORM=offscreen` and swaps the activity DB to a tmp dir via `temp_activity_db` (autouse). Never read/write the real `%APPDATA%/Automat/activity.db` in tests.
- `test_gui_smoke.py` additionally monkeypatches `SETTINGS_FILE`/`BOOKMARKS_FILE` to `tmp_path`. Do the same for any new GUI test.
- GUI smoke pattern: build `AutomatApp()` offscreen and call `win.show_page(key)` for every key in `PAGES` — catches build-time import errors.

## Architecture rules

- New page: subclass `PageWidget` in `automat/ui/page_base.py`, use `header()`/`card()`, styling via `objectName` + QSS in `automat/config.py` only. Register in `PAGES` list in `automat/app.py` as `(icon, i18n_key, page_key, class)`; separators are `("", None, None, None)`.
- Background work: use `automat/core/worker.py` (`Worker` / `run_in_background`, QThreadPool+QRunnable). Never raw `threading.Thread` for UI-adjacent tasks.
- Cross-thread UI updates: use `safe()` from `automat/util.py` (signal marshaller). `QTimer.singleShot(0, ...)` silently never fires from QThreadPool workers (no event loop); `schedule()` is legacy one-shot only.
- Persistence — use helpers, never raw file/DB access:
  - JSON (`%APPDATA%/Automat/settings.json`, `tasks.json`, `bookmarks.json`): `automat/core/json_io.py` `load_json`/`save_json` (atomic write + quarantines corrupt files to `.corrupt`). `DATA_DIR` defined in `automat/config.py`.
  - SQLite (`activity.db`, clipboard): `automat/core/db.py` `connect()` (WAL + busy timeout + auto-close) and `@retry_on_lock` for writes; short-lived connections only. Deleting a DB must remove `-wal`/`-shm` sidecars via `delete_database()`.
- i18n is RU/EN via `automat/i18n.py` — new user-facing strings need both keys; themes via `automat/core/theme_manager.py`.
