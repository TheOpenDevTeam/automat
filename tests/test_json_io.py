"""Tests for the JSON persistence helper (quarantine + atomic save)."""
import json
from pathlib import Path

from automat.core import json_io


def test_missing_file_returns_default(tmp_path):
    p = tmp_path / "nope.json"
    assert json_io.load_json(p, {"a": 1}) == {"a": 1}
    assert p.exists() is False


def test_default_is_copied_not_shared(tmp_path):
    p = tmp_path / "n.json"
    default = {"tags": []}
    got = json_io.load_json(p, default)
    got["tags"].append("x")
    assert default["tags"] == []


def test_valid_file_loaded(tmp_path):
    p = tmp_path / "ok.json"
    p.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
    assert json_io.load_json(p, {}) == {"theme": "dark"}


def test_corrupt_file_quarantined_not_deleted(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text('{"theme": "dark", "lang": ', encoding="utf-8")

    assert json_io.load_json(p, {"theme": "light"}) == {"theme": "light"}

    assert not p.exists(), "corrupt file should be moved aside"
    backup = tmp_path / "settings.json.corrupt"
    assert backup.exists()
    assert backup.read_text(encoding="utf-8").startswith('{"theme"')


def test_corrupt_file_overwrites_previous_quarantine(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("not json at all", encoding="utf-8")
    json_io.load_json(p, {})
    p.write_text("still not json", encoding="utf-8")
    json_io.load_json(p, {})
    backup = tmp_path / "s.json.corrupt"
    assert backup.read_text(encoding="utf-8") == "still not json"


def test_non_dict_content_is_returned_as_is(tmp_path):
    p = tmp_path / "list.json"
    p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert json_io.load_json(p, []) == [1, 2, 3]


def test_save_json_roundtrip(tmp_path):
    p = tmp_path / "sub" / "data.json"
    assert json_io.save_json(p, {"b": 2, "a": [1, "ю"]}) is True
    assert json.loads(p.read_text(encoding="utf-8")) == {"b": 2, "a": [1, "ю"]}


def test_save_json_leaves_no_temp_files(tmp_path):
    p = tmp_path / "data.json"
    json_io.save_json(p, {"a": 1})
    leftovers = [f for f in tmp_path.iterdir() if f.suffix == ".tmp"]
    assert leftovers == []
    assert p.exists()


def test_save_json_creates_parent_dirs(tmp_path):
    p = tmp_path / "a" / "b" / "c.json"
    json_io.save_json(p, {})
    assert p.exists()


def test_save_json_overwrites_existing(tmp_path):
    p = tmp_path / "d.json"
    json_io.save_json(p, {"v": 1})
    json_io.save_json(p, {"v": 2})
    assert json.loads(p.read_text(encoding="utf-8")) == {"v": 2}
