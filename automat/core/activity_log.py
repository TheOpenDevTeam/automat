"""
AUTOMAT — Модуль аналитики v1.0
Хранит реальную статистику операций в SQLite.
"""
import sqlite3, datetime, os, logging
from pathlib import Path

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
    c = sqlite3.connect(str(_DB_FILE))
    c.row_factory = sqlite3.Row
    return c

def _init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, event TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ok',
            detail TEXT DEFAULT '', count INTEGER DEFAULT 1)""")
        c.commit()
_init()

def log(event: str, status: str = STATUS_OK, detail: str = "", count: int = 1):
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with _conn() as c:
            c.execute("INSERT INTO events (ts,event,status,detail,count) VALUES (?,?,?,?,?)",
                      (ts, event, status, detail, count))
            c.commit()
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
