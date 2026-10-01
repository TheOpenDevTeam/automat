"""
Clipboard history — SQLite store with pinning, dedup, and search.
Monitor is process-wide and idempotent: call ensure_monitoring(qapp) once.
"""

import sqlite3
import datetime
import os
import logging
from pathlib import Path

from automat.core import db

LOG = logging.getLogger("automat.clipboard")

_APP_DIR = Path(os.getenv("APPDATA", Path.home())) / "Automat"
_DB_FILE = _APP_DIR / "clipboard.db"
_APP_DIR.mkdir(parents=True, exist_ok=True)

MAX_TEXT_LEN = 20000
MAX_ITEMS = 200

_monitoring = False


def _conn():
    return db.connect(_DB_FILE)


def _init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, text TEXT NOT NULL,
            pinned INTEGER NOT NULL DEFAULT 0)""")
        c.commit()


_init()


@db.retry_on_lock
def _insert_clip(text: str) -> bool:
    """Read-dedup + insert + prune in one transaction. May raise on lock."""
    with _conn() as c:
        last = c.execute("SELECT text FROM clips ORDER BY id DESC LIMIT 1").fetchone()
        if last and last["text"] == text:
            return False
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO clips (ts, text, pinned) VALUES (?,?,0)", (ts, text))
        # prune unpinned beyond limit
        c.execute("""DELETE FROM clips WHERE pinned = 0 AND id NOT IN
                     (SELECT id FROM clips WHERE pinned = 0 ORDER BY id DESC LIMIT ?)""",
                  (MAX_ITEMS,))
        c.commit()
    return True


def push(text: str) -> bool:
    """Store clipboard text. Returns True if stored (not dup/empty)."""
    if not text or not text.strip():
        return False
    text = text[:MAX_TEXT_LEN]
    try:
        return _insert_clip(text)
    except Exception as e:
        LOG.error("push failed: %s", e)
        return False


def list_clips(query: str = "", limit: int = 100) -> list:
    rows = []
    try:
        with _conn() as c:
            if query:
                cur = c.execute(
                    "SELECT id, ts, text, pinned FROM clips WHERE text LIKE ? "
                    "ORDER BY pinned DESC, id DESC LIMIT ?",
                    (f"%{query}%", limit))
            else:
                cur = c.execute(
                    "SELECT id, ts, text, pinned FROM clips "
                    "ORDER BY pinned DESC, id DESC LIMIT ?", (limit,))
            for r in cur:
                rows.append({"id": r["id"], "ts": r["ts"], "text": r["text"],
                             "pinned": bool(r["pinned"])})
    except Exception as e:
        LOG.error("list_clips failed: %s", e)
    return rows


@db.retry_on_lock
def _set_pinned_op(clip_id: int, pinned: bool):
    with _conn() as c:
        c.execute("UPDATE clips SET pinned = ? WHERE id = ?", (1 if pinned else 0, clip_id))
        c.commit()


def set_pinned(clip_id: int, pinned: bool) -> bool:
    try:
        _set_pinned_op(clip_id, pinned)
        return True
    except Exception as e:
        LOG.error("set_pinned failed: %s", e)
        return False


@db.retry_on_lock
def _delete_op(clip_id: int):
    with _conn() as c:
        c.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
        c.commit()


def delete(clip_id: int) -> bool:
    try:
        _delete_op(clip_id)
        return True
    except Exception as e:
        LOG.error("delete failed: %s", e)
        return False


@db.retry_on_lock
def _clear_op(unpinned_only: bool):
    with _conn() as c:
        if unpinned_only:
            c.execute("DELETE FROM clips WHERE pinned = 0")
        else:
            c.execute("DELETE FROM clips")
        c.commit()


def clear(unpinned_only: bool = True) -> bool:
    try:
        _clear_op(unpinned_only)
        return True
    except Exception as e:
        LOG.error("clear failed: %s", e)
        return False


def count() -> int:
    try:
        with _conn() as c:
            return int(c.execute("SELECT COUNT(*) FROM clips").fetchone()[0] or 0)
    except Exception:
        return 0


def ensure_monitoring(qapp) -> bool:
    """Attach to QApplication.clipboard().dataChanged once. Idempotent."""
    global _monitoring
    if _monitoring:
        return True
    try:
        cb = qapp.clipboard()
        cb.dataChanged.connect(lambda: _on_clipboard(cb))
        _monitoring = True
        return True
    except Exception as e:
        LOG.error("ensure_monitoring failed: %s", e)
        return False


def _on_clipboard(cb):
    try:
        if cb.mimeData().hasText():
            push(cb.text())
    except Exception as e:
        LOG.error("clipboard read failed: %s", e)


def is_monitoring() -> bool:
    return _monitoring
