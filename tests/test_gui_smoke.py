"""
Headless GUI smoke tests: build the whole window and every page offscreen.

These guard against the class of bugs that only appear when the UI is
actually constructed — missing imports reached at widget-build time
(e.g. `csv` in convert_pro), a hard dependency that breaks startup
(PyQtChart), or a drop that never reaches the target page.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt5.QtWidgets", reason="PyQt5 not installed")

from PyQt5.QtCore import QMimeData, QPoint, Qt, QUrl
from PyQt5.QtWidgets import QApplication

import automat.app as app_module
from automat.app import AutomatApp


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture()
def window(qapp, monkeypatch, tmp_path):
    # Never touch the developer's real settings/bookmarks.
    monkeypatch.setattr(app_module, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.setattr(app_module, "BOOKMARKS_FILE", str(tmp_path / "bookmarks.json"))
    win = AutomatApp()
    yield win
    win.close()


def _open_every_page(win):
    """Build every registered page; a build-time ImportError/NameError fails here."""
    for _icon, _name, key, _cls in app_module.PAGES:
        if key is None:
            continue
        win.show_page(key)
        assert key in win._pages, f"page {key} was not created"


def test_all_pages_build(window):
    _open_every_page(window)


def _drop_paths(window, paths, action=Qt.CopyAction):
    """Feed paths through the real dropEvent, as if dragged onto the window."""
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(p) for p in paths])
    # Synthetic drop: pos, actions, mime, buttons, modifiers, type.
    from PyQt5.QtGui import QDropEvent
    ev = QDropEvent(
        QPoint(10, 10), action, mime, Qt.LeftButton, Qt.NoModifier,
        QDropEvent.Drop,
    )
    ev.acceptProposedAction()
    window.dropEvent(ev)


def test_drop_text_file_lands_in_editor(window, tmp_path):
    src = tmp_path / "dropped.txt"
    src.write_text("hello drop", encoding="utf-8")
    _drop_paths(window, [str(src)])
    page = window._pages.get("text")
    assert page is not None
    assert page.editor.toPlainText() == "hello drop"


def test_drop_convertible_files_land_in_convert_list(window, tmp_path):
    f1 = tmp_path / "a.csv"
    f2 = tmp_path / "b.csv"
    for f in (f1, f2):
        f.write_text("x,y\n1,2\n", encoding="utf-8")
    _drop_paths(window, [str(f1), str(f2)])
    page = window._pages.get("convert")
    assert page is not None
    # QUrl normalizes separators to "/" — compare paths, not raw strings.
    got = {Path(p).resolve() for p in page.files}
    assert got == {f1.resolve(), f2.resolve()}
    assert page.file_list.count() == 2


def test_drop_folder_lands_in_fileops(window, tmp_path):
    d = tmp_path / "folder"
    d.mkdir()
    _drop_paths(window, [str(d)])
    page = window._pages.get("fileops")
    assert page is not None
    assert Path(page.ren_path.text()).resolve() == d.resolve()


def test_convert_csv_roundtrip_needs_csv_import(window, tmp_path):
    """Regression: convert_pro used `csv` without importing it (NameError)."""
    page = window.show_page("convert")
    page = window._pages["convert"]
    src = tmp_path / "in.csv"
    src.write_text("a,b\n1,2\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    page.files.append(str(src))
    page.conv_type.setCurrentIndex(5)  # "CSV -> Excel"
    page.out_path.setText(str(out_dir))
    page.stop_flag = False
    page._run()
    assert (out_dir / "in.xlsx").exists()
