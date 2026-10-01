import gc
import os
import sys
import tempfile
from pathlib import Path

# Tests import the package as `automat.*`, so the project root must be on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Headless by default: never open a real window during the test run.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(autouse=True)
def temp_activity_db(monkeypatch):
    """Point the activity log at a throwaway database for every test.

    Without this the tests read/write the developer's real history and
    assertions depending on an empty DB fail intermittently.
    """
    tmp = tempfile.mkdtemp(prefix="automat_test_")
    db_path = Path(tmp) / "activity.db"

    import automat.core.activity_log as al
    monkeypatch.setattr(al, "_APP_DIR", Path(tmp))
    monkeypatch.setattr(al, "_DB_FILE", db_path)
    al._init()

    yield

    gc.collect()
    for f in Path(tmp).iterdir():
        try:
            f.unlink()
        except (PermissionError, OSError):
            pass
    try:
        os.rmdir(tmp)
    except OSError:
        pass
