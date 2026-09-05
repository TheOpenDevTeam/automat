"""
Tests for the activity logging subsystem.

Uses a temporary SQLite database for each test to avoid polluting
the real database and to allow parallel execution.
"""

import gc
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    """
    Redirect the activity log to a temporary database file.
    After the test completes, close all connections and remove files.
    """
    tmp = tempfile.mkdtemp()
    db_path = Path(tmp) / "test_activity.db"

    monkeypatch.setattr("core.activity_log._APP_DIR", Path(tmp))
    monkeypatch.setattr("core.activity_log._DB_FILE", db_path)

    import core.activity_log as al
    al._init()
    yield

    # Force garbage collection to release SQLite file handles on Windows.
    # Without this, Windows keeps the .db file locked briefly after close.
    gc.collect()

    for f in Path(tmp).iterdir():
        try:
            f.unlink()
        except PermissionError:
            pass
    try:
        os.rmdir(tmp)
    except OSError:
        pass


def test_log_and_get_totals():
    """Logging items with the same event type should accumulate correctly."""
    from core.activity_log import log, get_totals, EVENT_CONVERT, STATUS_OK

    log(EVENT_CONVERT, STATUS_OK, "test", 3)
    log(EVENT_CONVERT, STATUS_OK, "test2", 2)

    totals = get_totals()
    assert totals[EVENT_CONVERT] == 5


def test_get_recent_events():
    """Recent events should be returned in reverse-chronological order."""
    from core.activity_log import log, get_recent_events, EVENT_SEND, STATUS_OK

    log(EVENT_SEND, STATUS_OK, "batch1", 10)
    events = get_recent_events(5)
    assert len(events) >= 1
    assert events[0]["event"] == EVENT_SEND
    assert events[0]["detail"] == "batch1"


def test_success_rate():
    """Success rate should be correct across OK and ERROR statuses."""
    from core.activity_log import log, get_success_rate, EVENT_HASH, STATUS_OK, STATUS_ERROR

    log(EVENT_HASH, STATUS_OK, "ok1", 1)
    log(EVENT_HASH, STATUS_OK, "ok2", 1)
    log(EVENT_HASH, STATUS_ERROR, "fail1", 1)

    rate = get_success_rate()
    assert rate == pytest.approx(2 / 3)
