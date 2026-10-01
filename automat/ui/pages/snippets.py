import json
import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.config import DATA_DIR
from automat.ui.page_base import PageWidget
from automat.core import json_io

SNIPPETS_FILE = str(DATA_DIR / "snippets.json")

VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

DEFAULT_SNIPPETS = {
    "Python": [
        {"name": "HTTP Request", "tags": ["http", "requests"], "code": "import requests\n\nr = requests.get('https://api.example.com')\nprint(r.json())"},
        {"name": "HTTP POST JSON", "tags": ["http", "post"], "code": "import requests\n\nr = requests.post('{{url}}', json={'key': '{{value}}'}, timeout=15)\nr.raise_for_status()\nprint(r.json())"},
        {"name": "Read File", "tags": ["file", "io"], "code": "with open('file.txt', 'r', encoding='utf-8') as f:\n    content = f.read()\n    print(content)"},
        {"name": "List Files", "tags": ["os", "files"], "code": "import os\n\nfor f in os.listdir('.'):\n    print(f)"},
        {"name": "CSV Read", "tags": ["csv"], "code": "import csv\n\nwith open('{{file}}.csv', encoding='utf-8') as f:\n    for row in csv.DictReader(f):\n        print(row)"},
        {"name": "Timer", "tags": ["time"], "code": "import time\n\nt0 = time.perf_counter()\n# ... code ...\nprint(f'{time.perf_counter() - t0:.3f}s')"},
    ],
    "SQL": [
        {"name": "Select All", "tags": ["select"], "code": "SELECT * FROM {{table}} LIMIT 10;"},
        {"name": "Create Table", "tags": ["ddl"], "code": "CREATE TABLE {{table}} (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL,\n    email TEXT UNIQUE\n);"},
        {"name": "Upsert (Postgres)", "tags": ["postgres", "upsert"], "code": "INSERT INTO {{table}} ({{cols}}) VALUES ({{vals}})\nON CONFLICT ({{key}}) DO UPDATE SET {{cols}} = EXCLUDED.{{cols}};"},
    ],
    "Bash": [
        {"name": "Git Status", "tags": ["git"], "code": "git status\ngit log --oneline -5"},
        {"name": "Find Files", "tags": ["find"], "code": "find . -name '{{mask}}' -type f"},
        {"name": "Port Listen", "tags": ["net"], "code": "netstat -ano | findstr :{{port}}"},
    ],
    "Regex": [
        {"name": "Email", "tags": ["regex"], "code": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"},
        {"name": "Phone RU", "tags": ["regex", "phone"], "code": r"\+7[0-9]{10}"},
        {"name": "URL", "tags": ["regex"], "code": r"https?://[^\s/$.?#].[^\s]*"},
        {"name": "IPv4", "tags": ["regex", "ip"], "code": r"\b(?:\d{1,3}\.){3}\d{1,3}\b"},
        {"name": "Date ISO", "tags": ["regex", "date"], "code": r"\b\d{4}-\d{2}-\d{2}\b"},
    ],
    "JavaScript": [
        {"name": "Fetch JSON", "tags": ["fetch", "http"], "code": "const r = await fetch('{{url}}');\nconst data = await r.json();\nconsole.log(data);"},
        {"name": "Debounce", "tags": ["util"], "code": "const debounce = (fn, ms) => {\n  let t;\n  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };\n};"},
    ],
    "curl": [
        {"name": "GET JSON", "tags": ["http", "get"], "code": "curl -s '{{url}}' | python -m json.tool"},
        {"name": "POST JSON", "tags": ["http", "post"], "code": "curl -s -X POST '{{url}}' -H 'Content-Type: application/json' -d '{{\"{{key}}\": \"{{value}}\"}}'"},
    ],
}


def find_vars(code):
    """Extract unique {{var}} names in order of appearance."""
    seen = []
    for m in VAR_RE.finditer(code or ""):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def render_template(code, values):
    """Replace {{var}} with values; unknown vars left as-is."""
    def _sub(m):
        return str(values.get(m.group(1), m.group(0)))
    return VAR_RE.sub(_sub, code or "")


class VarDialog(QDialog):
    """Fill {{var}} values and preview rendered result."""
    def __init__(self, parent, code):
        super().__init__(parent)
        tr = parent.app.i18n.tr
        self.setWindowTitle(tr("snippet_vars_title"))
        self.setMinimumWidth(420)
        self.code = code
        self.vars = find_vars(code)
        layout = QVBoxLayout(self)
        self.edits = {}
        form = QFormLayout()
        for v in self.vars:
            e = QLineEdit()
            e.textChanged.connect(self._preview)
            self.edits[v] = e
            form.addRow(v, e)
        layout.addLayout(form)
        layout.addWidget(QLabel(tr("snippet_vars_preview")))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setObjectName("code_output")
        self.preview.setMaximumHeight(180)
        layout.addWidget(self.preview)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self._preview()

    def _preview(self):
        self.preview.setPlainText(render_template(self.code, self.values()))

    def values(self):
        return {k: e.text() for k, e in self.edits.items()}


class SnippetsPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.data = {}
        self.current_cat = ""
        self._search_mode = False
        self.build()
        self._load()

    def build(self):
        tr = self.app.i18n.tr
        self.header("snippets", tr("snippet_title"), tr("snippet_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("snippet_categories_card"))
        outer.addWidget(left)
        self.cat_list = QListWidget()
        self.cat_list.itemClicked.connect(self._show_snippets)
        ll.addWidget(self.cat_list)

        add_cat_row = QHBoxLayout()
        self.new_cat = QLineEdit()
        self.new_cat.setPlaceholderText(tr("snippet_new_category"))
        self.new_cat.returnPressed.connect(self._add_category)
        add_cat_row.addWidget(self.new_cat)
        add_cat_btn = QPushButton("+")
        add_cat_btn.setFixedWidth(40)
        add_cat_btn.clicked.connect(self._add_category)
        add_cat_row.addWidget(add_cat_btn)
        del_cat_btn = QPushButton("−")
        del_cat_btn.setFixedWidth(40)
        del_cat_btn.setObjectName("danger")
        del_cat_btn.setToolTip(tr("snippet_del_category"))
        del_cat_btn.clicked.connect(self._del_category)
        add_cat_row.addWidget(del_cat_btn)
        ll.addLayout(add_cat_row)

        right, inner_right, rl = self.card(tr("snippet_snippets_card"))
        outer.addWidget(right, 1)

        # search row
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("snippet_search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._on_search)
        search_row.addWidget(self.search, 1)
        # import/export
        imp_btn = QPushButton(tr("snippet_import"))
        imp_btn.clicked.connect(self._import_json)
        search_row.addWidget(imp_btn)
        exp_btn = QPushButton(tr("snippet_export"))
        exp_btn.clicked.connect(self._export_json)
        search_row.addWidget(exp_btn)
        rl.addLayout(search_row)

        self.snip_list = QListWidget()
        self.snip_list.itemClicked.connect(self._show_code)
        self.snip_list.itemDoubleClicked.connect(lambda item: self._copy_code())
        rl.addWidget(self.snip_list)

        rl.addWidget(QLabel(tr("snippet_name_label")))
        name_row = QHBoxLayout()
        self.snip_name = QLineEdit()
        self.snip_name.setPlaceholderText("Snippet name")
        name_row.addWidget(self.snip_name, 1)
        self.snip_tags = QLineEdit()
        self.snip_tags.setPlaceholderText(tr("snippet_tags_hint"))
        self.snip_tags.setMaximumWidth(220)
        name_row.addWidget(self.snip_tags)
        rl.addLayout(name_row)

        rl.addWidget(QLabel(tr("snippet_code_label")))
        self.snip_code = QPlainTextEdit()
        self.snip_code.setPlaceholderText("Paste code here... Use {{var}} for templates.")
        self.snip_code.setObjectName("code_editor")
        rl.addWidget(self.snip_code, 1)

        self.vars_hint = QLabel("")
        self.vars_hint.setObjectName("text_muted")
        rl.addWidget(self.vars_hint)
        self.snip_code.textChanged.connect(self._update_vars_hint)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for txt, fn, obj in [("+ " + tr("snippet_add"), self._add_snippet, "accent"),
                              (tr("snippet_update"), self._update_snippet, "accent2"),
                              (tr("snippet_render"), self._render_vars, None),
                              (tr("snippet_delete"), self._del_snippet, "danger"),
                              (tr("snippet_copy"), self._copy_code, None),
                              (tr("snippet_save"), self._save, "success")]:
            b = QPushButton(txt)
            b.setMinimumWidth(80)
            if obj:
                b.setObjectName(obj)
            b.clicked.connect(fn)
            btn_row.addWidget(b)
        rl.addLayout(btn_row)

        # send-to row
        send_row = QHBoxLayout()
        send_row.addWidget(QLabel(tr("snippet_send_to")))
        self.send_combo = QComboBox()
        self.send_combo.addItems([
            tr("snippet_send_text"),
            tr("snippet_send_api_body"),
            tr("snippet_send_api_fmt"),
        ])
        send_row.addWidget(self.send_combo, 1)
        send_btn = QPushButton(tr("snippet_send"))
        send_btn.setObjectName("accent")
        send_btn.clicked.connect(self._send_to)
        send_row.addWidget(send_btn)
        rl.addLayout(send_row)

    # ── data ──
    def _load(self):
        data = json_io.load_json(SNIPPETS_FILE, None)
        if data is None:
            self.data = dict(DEFAULT_SNIPPETS)
            self._save()
        elif isinstance(data, dict):
            self.data = data
        else:
            self.data = dict(DEFAULT_SNIPPETS)
        # normalize old entries
        for cat, lst in self.data.items():
            if not isinstance(lst, list):
                self.data[cat] = []
                continue
            for s in lst:
                if isinstance(s, dict):
                    s.setdefault("tags", [])
        self._refresh_cats()

    def _save(self):
        json_io.save_json(SNIPPETS_FILE, self.data)

    def _refresh_cats(self):
        self.cat_list.clear()
        for cat in self.data:
            self.cat_list.addItem(f"{cat} ({len(self.data[cat])})")

    def _cat_name(self, item):
        if item is None:
            return ""
        txt = item.text()
        # strip " (N)" suffix
        if txt.endswith(")") and " (" in txt:
            return txt.rsplit(" (", 1)[0]
        return txt

    # ── list / search ──
    def _show_snippets(self, item):
        self._search_mode = False
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.current_cat = self._cat_name(item)
        self._fill_list(self.data.get(self.current_cat, []), show_cat=False)

    def _fill_list(self, snips, show_cat=False):
        self.snip_list.clear()
        self._listed = snips
        for s in snips:
            label = f"[{s.get('_cat', '')}] {s['name']}" if show_cat else s["name"]
            tags = ", ".join(s.get("tags", []))
            item = QListWidgetItem(label)
            if tags:
                item.setToolTip(tags)
            self.snip_list.addItem(item)

    def _on_search(self, text):
        q = text.strip().lower()
        if not q:
            self._search_mode = False
            if self.current_cat:
                self._fill_list(self.data.get(self.current_cat, []))
            else:
                self.snip_list.clear()
            return
        self._search_mode = True
        found = []
        for cat, lst in self.data.items():
            for s in lst:
                hay = (s["name"] + " " + s.get("code", "") + " " + " ".join(s.get("tags", []))).lower()
                if q in hay:
                    entry = dict(s)
                    entry["_cat"] = cat
                    found.append(entry)
        self._fill_list(found, show_cat=True)

    def _show_code(self, item):
        lst = getattr(self, "_listed", [])
        idx = self.snip_list.row(item)
        if 0 <= idx < len(lst):
            s = lst[idx]
            self.snip_name.setText(s["name"])
            self.snip_tags.setText(", ".join(s.get("tags", [])))
            self.snip_code.setPlainText(s.get("code", ""))

    def _update_vars_hint(self):
        tr = self.app.i18n.tr
        vs = find_vars(self.snip_code.toPlainText())
        self.vars_hint.setText(tr("snippet_vars_found", vars=", ".join(vs)) if vs else "")

    # ── CRUD ──
    def _add_category(self):
        name = self.new_cat.text().strip()
        if name and name not in self.data:
            self.data[name] = []
            self._refresh_cats()
            self.new_cat.clear()
            self._save()

    def _del_category(self):
        tr = self.app.i18n.tr
        item = self.cat_list.currentItem()
        if not item:
            return
        cat = self._cat_name(item)
        if QMessageBox.question(self, tr("snippet_error"),
                                tr("snippet_del_category_confirm", cat=cat)) == QMessageBox.Yes:
            self.data.pop(cat, None)
            self.current_cat = ""
            self.snip_list.clear()
            self._refresh_cats()
            self._save()

    def _parse_tags(self):
        return [t.strip() for t in self.snip_tags.text().split(",") if t.strip()]

    def _add_snippet(self):
        tr = self.app.i18n.tr
        if not self.current_cat:
            QMessageBox.warning(self, tr("snippet_error"), tr("snippet_select_category"))
            return
        name = self.snip_name.text().strip()
        code = self.snip_code.toPlainText()
        if not name:
            QMessageBox.warning(self, tr("snippet_error"), tr("snippet_enter_name"))
            return
        self.data.setdefault(self.current_cat, []).append(
            {"name": name, "code": code, "tags": self._parse_tags()})
        self._refresh_cats()
        self._fill_list(self.data[self.current_cat])
        self._save()

    def _update_snippet(self):
        tr = self.app.i18n.tr
        item = self.snip_list.currentItem()
        if not item or self._search_mode:
            QMessageBox.information(self, tr("snippet_error"), tr("snippet_update_hint"))
            return
        name = self.snip_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("snippet_error"), tr("snippet_enter_name"))
            return
        lst = self.data.get(self.current_cat, [])
        idx = self.snip_list.row(item)
        if 0 <= idx < len(lst):
            lst[idx] = {"name": name, "code": self.snip_code.toPlainText(), "tags": self._parse_tags()}
            self._fill_list(lst)
            self._save()

    def _del_snippet(self):
        item = self.snip_list.currentItem()
        if not item:
            return
        if self._search_mode:
            # delete from its home category
            lst = getattr(self, "_listed", [])
            idx = self.snip_list.row(item)
            if 0 <= idx < len(lst):
                entry = lst[idx]
                cat = entry.get("_cat", "")
                self.data[cat] = [s for s in self.data.get(cat, []) if s["name"] != entry["name"]]
                self._on_search(self.search.text())
                self._refresh_cats()
                self._save()
            return
        if not self.current_cat:
            return
        self.data[self.current_cat] = [s for s in self.data[self.current_cat] if s["name"] != item.text()]
        self._fill_list(self.data[self.current_cat])
        self._refresh_cats()
        self._save()

    # ── actions ──
    def _current_code(self):
        return self.snip_code.toPlainText()

    def _copy_code(self):
        code = self._current_code()
        if code:
            QApplication.clipboard().setText(code)

    def _render_vars(self):
        tr = self.app.i18n.tr
        code = self._current_code()
        if not find_vars(code):
            QMessageBox.information(self, tr("snippet_error"), tr("snippet_no_vars"))
            return
        dlg = VarDialog(self, code)
        if dlg.exec_() == QDialog.Accepted:
            self.snip_code.setPlainText(render_template(code, dlg.values()))

    def _send_to(self):
        tr = self.app.i18n.tr
        code = self._current_code()
        if not code:
            return
        # auto-render if template vars present
        if find_vars(code):
            dlg = VarDialog(self, code)
            if dlg.exec_() != QDialog.Accepted:
                return
            code = render_template(code, dlg.values())
        idx = self.send_combo.currentIndex()
        try:
            if idx == 0:  # text tools
                self.app.show_page("text")
                page = self.app._pages.get("text")
                if page and hasattr(page, "editor"):
                    page.editor.setPlainText(code)
            elif idx == 1:  # api body
                self.app.show_page("api")
                page = self.app._pages.get("api")
                if page and hasattr(page, "body_input"):
                    page.body_input.setPlainText(code)
            elif idx == 2:  # api formatter
                self.app.show_page("api")
                page = self.app._pages.get("api")
                if page and hasattr(page, "fmt_input"):
                    page.fmt_input.setPlainText(code)
        except Exception as e:
            QMessageBox.warning(self, tr("snippet_error"), str(e))

    # ── import / export ──
    def _import_json(self):
        tr = self.app.i18n.tr
        fp, _ = QFileDialog.getOpenFileName(self, tr("snippet_import"), "", "JSON (*.json)")
        if not fp:
            return
        try:
            with open(fp, encoding="utf-8") as f:
                obj = json.load(f)
            added = 0
            if isinstance(obj, dict):
                for cat, lst in obj.items():
                    if not isinstance(lst, list):
                        continue
                    bucket = self.data.setdefault(cat, [])
                    for s in lst:
                        if isinstance(s, dict) and s.get("name"):
                            s.setdefault("code", "")
                            s.setdefault("tags", [])
                            bucket.append({"name": s["name"], "code": s["code"], "tags": s["tags"]})
                            added += 1
            self._refresh_cats()
            self._save()
            QMessageBox.information(self, tr("snippet_saved"), tr("snippet_imported", n=added))
        except Exception as e:
            QMessageBox.warning(self, tr("snippet_error"), str(e))

    def _export_json(self):
        tr = self.app.i18n.tr
        fp, _ = QFileDialog.getSaveFileName(self, tr("snippet_export"), "snippets.json", "JSON (*.json)")
        if not fp:
            return
        try:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, tr("snippet_saved"), f"✓ {fp}")
        except Exception as e:
            QMessageBox.warning(self, tr("snippet_error"), str(e))
