"""
Shared SQLite plumbing.

Every store in AUTOMAT opens short-lived connections from different threads
(clipboard monitor, worker pool, APScheduler jobs, the GUI). Without a busy
timeout they collide on the file lock and drop writes with "database is
locked". WAL lets readers run while a writer is active, and the busy timeout
makes SQLite retry internally instead of failing immediately.
"""

import functools
import logging
import sqlite3
import time

LOG = logging.getLogger("automat.db")

BUSY_TIMEOUT_MS = 5000
_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF = 0.05


class _ClosingConnection(sqlite3.Connection):
    """Connection that closes when its `with` block exits.

    sqlite3's `with conn` only commits or rolls back — it never closes the
    handle. Every call site in AUTOMAT opens a short-lived connection, so
    without this they pile up and keep the DB file locked (notably on Windows,
    where an open handle also blocks deleting the file).
    """

    def __exit__(self, exc_type, exc, tb):
        try:
            return super().__exit__(exc_type, exc, tb)
        finally:
            self.close()


def connect(db_file):
    """Open a connection tuned for concurrent short-lived use."""
    conn = sqlite3.connect(
        str(db_file),
        timeout=BUSY_TIMEOUT_MS / 1000.0,
        factory=_ClosingConnection,
    )
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
    except sqlite3.Error as exc:
        LOG.debug("WAL not enabled for %s: %s", db_file, exc)
    return conn


def is_locked(exc) -> bool:
    msg = str(exc).lower()
    return "locked" in msg or "busy" in msg


def delete_database(db_file) -> None:
    """Remove a database together with its WAL/SHM sidecars.

    Deleting only the .db would leave stale -wal/-shm files behind, and the
    next connection could then resurrect (or fail to open) old content.
    """
    import os

    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(str(db_file) + suffix)
        except FileNotFoundError:
            pass
        except OSError as exc:
            LOG.debug("could not remove %s%s: %s", db_file, suffix, exc)


def retry_on_lock(func):
    """Retry a write a few times when SQLite reports the DB is locked/busy.

    The busy timeout already covers most contention; this is the safety net
    for bursts where several writers keep re-acquiring the lock.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last = None
        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as exc:
                if not is_locked(exc):
                    raise
                last = exc
                time.sleep(_RETRY_BACKOFF * attempt)
                LOG.debug("locked (attempt %d/%d) in %s",
                          attempt, _RETRY_ATTEMPTS, func.__name__)
        raise last

    return wrapper
