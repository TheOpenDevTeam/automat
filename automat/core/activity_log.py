"""
AUTOMAT — Модуль аналитики v1.0
Хранит реальную статистику операций в SQLite.
"""
import sqlite3, datetime, os, logging
from pathlib import Path

from automat.core import db

LOG = logging.getLogger("automat.activity")

_APP_DIR = Path(os.getenv("APPDATA", Path.home())) / "Automat"
_DB_FILE = _APP_DIR / "activity.db"
_APP_DIR.mkdir(parents=True, exist_ok=True)

EVENT_CONVERT  = "convert"
EVENT_SEND     = "send"
EVENT_HASH     = "hash"
EVENT_SCHEDULE = "schedule"
EVENT_FILEOP   = "fileop"
EVENT_CLEAN    = "clean"
EVENT_DATAGEN  = "datagen"
EVENT_TEXT     = "text"

STATUS_OK    = "ok"
STATUS_ERROR = "error"
STATUS_SKIP  = "skip"

def _conn():
    return db.connect(_DB_FILE)

def _init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, event TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ok',
            detail TEXT DEFAULT '', count INTEGER DEFAULT 1)""")
        c.commit()
_init()

@db.retry_on_lock
def _insert_event(ts, event, status, detail, count):
    with _conn() as c:
        c.execute("INSERT INTO events (ts,event,status,detail,count) VALUES (?,?,?,?,?)",
                  (ts, event, status, detail, count))
        c.commit()


def log(event: str, status: str = STATUS_OK, detail: str = "", count: int = 1):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        _insert_event(ts, event, status, detail, count)
    except Exception as e:
        LOG.error("log failed: %s", e)

def get_totals() -> dict:
    result = {k: 0 for k in [EVENT_CONVERT, EVENT_SEND, EVENT_HASH, EVENT_SCHEDULE,
                               EVENT_FILEOP, EVENT_CLEAN, EVENT_DATAGEN, EVENT_TEXT]}
    try:
        with _conn() as c:
            for row in c.execute("SELECT event, SUM(count) as t FROM events WHERE status='ok' GROUP BY event"):
                if row["event"] in result:
                    result[row["event"]] = int(row["t"] or 0)
    except Exception as e:
        LOG.error("get_totals failed: %s", e)
    return result

def get_today_totals() -> dict:
    result = {k: 0 for k in [EVENT_CONVERT, EVENT_SEND, EVENT_HASH, EVENT_SCHEDULE]}
    try:
        today = datetime.date.today().isoformat()
        with _conn() as c:
            for row in c.execute(
                "SELECT event, SUM(count) as t FROM events WHERE status='ok' AND ts LIKE ? GROUP BY event",
                (f"{today}%",)):
                if row["event"] in result:
                    result[row["event"]] = int(row["t"] or 0)
    except Exception as e:
        LOG.error("get_today_totals failed: %s", e)
    return result

def get_recent_events(limit: int = 25) -> list:
    rows = []
    try:
        with _conn() as c:
            for row in c.execute(
                "SELECT ts,event,status,detail,count FROM events ORDER BY id DESC LIMIT ?", (limit,)):
                rows.append({"ts": row["ts"], "event": row["event"],
                             "status": row["status"], "detail": row["detail"] or "",
                             "count": row["count"]})
    except Exception as e:
        LOG.error("get_recent_events failed: %s", e)
    return rows

def get_stats_by_day(days: int = 7) -> list:
    result = []
    try:
        with _conn() as c:
            for row in c.execute("""
                SELECT substr(ts,1,10) as day, SUM(count) as total FROM events
                WHERE status='ok' AND ts >= date('now',?) GROUP BY day ORDER BY day""",
                (f"-{days} days",)):
                result.append({"date": row["day"], "total": int(row["total"] or 0)})
    except Exception as e:
        LOG.error("get_stats_by_day failed: %s", e)
    return result

def get_error_count(days: int = 7) -> int:
    try:
        with _conn() as c:
            return int(c.execute(
                "SELECT COUNT(*) FROM events WHERE status='error' AND ts >= date('now',?)",
                (f"-{days} days",)).fetchone()[0] or 0)
    except Exception as e:
        LOG.error("get_error_count failed: %s", e)
        return 0

def get_success_rate() -> float:
    try:
        with _conn() as c:
            total = c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            if not total: return 1.0
            ok = c.execute("SELECT COUNT(*) FROM events WHERE status='ok'").fetchone()[0]
            return ok / total
    except Exception as e:
        LOG.error("get_success_rate failed: %s", e)
        return 1.0


def export_csv(filepath: str) -> bool:
    """Export all events to CSV file."""
    import csv
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT id, ts, event, status, detail, count FROM events ORDER BY id"
            ).fetchall()
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Timestamp", "Event", "Status", "Detail", "Count"])
            for r in rows:
                writer.writerow([r["id"], r["ts"], r["event"], r["status"], r["detail"], r["count"]])
        return True
    except Exception as e:
        LOG.error("export_csv failed: %s", e)
        return False


def export_json(filepath: str) -> bool:
    """Export all events to JSON file."""
    import json
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT id, ts, event, status, detail, count FROM events ORDER BY id"
            ).fetchall()
        data = [
            {"id": r["id"], "ts": r["ts"], "event": r["event"],
             "status": r["status"], "detail": r["detail"], "count": r["count"]}
            for r in rows
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        LOG.error("export_json failed: %s", e)
        return False


def get_all_events_paginated(offset: int = 0, limit: int = 100, event_filter: str = None) -> list:
    """Get events with pagination and optional filter."""
    rows = []
    try:
        with _conn() as c:
            if event_filter:
                query = ("SELECT id, ts, event, status, detail, count FROM events "
                         "WHERE event = ? ORDER BY id DESC LIMIT ? OFFSET ?")
                params = (event_filter, limit, offset)
            else:
                query = ("SELECT id, ts, event, status, detail, count FROM events "
                         "ORDER BY id DESC LIMIT ? OFFSET ?")
                params = (limit, offset)
            for row in c.execute(query, params):
                rows.append({"id": row["id"], "ts": row["ts"], "event": row["event"],
                             "status": row["status"], "detail": row["detail"] or "",
                             "count": row["count"]})
    except Exception as e:
        LOG.error("get_all_events_paginated failed: %s", e)
    return rows


def search_events(query: str, limit: int = 50) -> list:
    """Full-text search across event details."""
    rows = []
    try:
        with _conn() as c:
            pattern = f"%{query}%"
            for row in c.execute(
                "SELECT id, ts, event, status, detail, count FROM events "
                "WHERE detail LIKE ? OR event LIKE ? "
                "ORDER BY id DESC LIMIT ?",
                (pattern, pattern, limit)):
                rows.append({"id": row["id"], "ts": row["ts"], "event": row["event"],
                             "status": row["status"], "detail": row["detail"] or "",
                             "count": row["count"]})
    except Exception as e:
        LOG.error("search_events failed: %s", e)
    return rows


def get_event_stats_by_type() -> list:
    """Get event counts grouped by type for the last 30 days."""
    rows = []
    try:
        with _conn() as c:
            for row in c.execute(
                "SELECT event, SUM(count) as total, "
                "SUM(CASE WHEN status='ok' THEN count ELSE 0 END) as ok_count "
                "FROM events WHERE ts >= date('now', '-30 days') "
                "GROUP BY event ORDER BY total DESC"):
                rows.append({"event": row["event"], "total": int(row["total"] or 0),
                             "ok": int(row["ok_count"] or 0)})
    except Exception as e:
        LOG.error("get_event_stats_by_type failed: %s", e)
    return rows


@db.retry_on_lock
def _clear_events():
    with _conn() as c:
        c.execute("DELETE FROM events")
        c.commit()


def clear_all_events() -> bool:
    """Clear all events from the database."""
    try:
        _clear_events()
        return True
    except Exception as e:
        LOG.error("clear_all_events failed: %s", e)
        return False
