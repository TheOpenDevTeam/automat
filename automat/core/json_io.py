"""
JSON persistence with corruption handling.

A truncated or hand-edited file used to be indistinguishable from a missing
one: every loader caught a bare `Exception` and quietly reset to defaults,
so a crash mid-write silently threw away settings, bookmarks or tasks.

`load_json` quarantines the damaged file next to the original instead of
overwriting it, and `save_json` writes atomically so a crash cannot truncate
the file in the first place.
"""

import copy
import json
import logging
import os
import tempfile
from pathlib import Path

LOG = logging.getLogger("automat.json")

ENCODING = "utf-8"


def quarantine(path, reason: str) -> Path:
    """Rename a damaged file to `<name>.corrupt` and return the new path.

    Overwrites any previous quarantine so repeated failures keep only the
    most recent evidence.
    """
    src = Path(path)
    dst = src.with_suffix(src.suffix + ".corrupt")
    try:
        os.replace(str(src), str(dst))
        LOG.warning("quarantined %s -> %s (%s)", src, dst, reason)
    except OSError as exc:
        LOG.error("could not quarantine %s: %s", src, exc)
    return dst


def load_json(path, default=None, *, encoding=ENCODING):
    """Read JSON from *path*.

    Returns a copy of *default* when the file is missing, and a copy of
    *default* when the file is corrupt — but in the corrupt case the file is
    first quarantined so nothing is destroyed.
    """
    p = Path(path)
    try:
        raw = p.read_text(encoding=encoding)
    except FileNotFoundError:
        return copy.deepcopy(default)
    except OSError as exc:
        LOG.error("could not read %s: %s", p, exc)
        return copy.deepcopy(default)

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        quarantine(p, str(exc))
        return copy.deepcopy(default)


def save_json(path, data, *, encoding=ENCODING, indent=2, sort_keys=False) -> bool:
    """Write JSON atomically: temp file in the same directory, then replace."""
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(p.parent), prefix=p.name + ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=indent,
                          sort_keys=sort_keys)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, str(p))
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        return True
    except OSError as exc:
        LOG.error("could not save %s: %s", p, exc)
        return False
