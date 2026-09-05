from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
from config import ACCENT, ACCENT2, GREEN, RED, DATA_DIR
from ui.page_base import PageWidget

SNIPPETS_FILE = str(DATA_DIR / "snippets.json")

DEFAULT_SNIPPETS = {
    "Python": [
        {"name": "HTTP Request", "code": "import requests\n\nr = requests.get('https://api.example.com')\nprint(r.json())"},
        {"name": "Read File", "code": "with open('file.txt', 'r', encoding='utf-8') as f:\n    content = f.read()\n    print(content)"},
        {"name": "List Files", "code": "import os\n\nfor f in os.listdir('.'):\n    print(f)"},
    ],
    "SQL": [
        {"name": "Select All", "code": "SELECT * FROM table_name LIMIT 10;"},
        {"name": "Create Table", "code": "CREATE TABLE users (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL,\n    email TEXT UNIQUE\n);"},
    ],
    "Bash": [
        {"name": "Git Status", "code": "git status\ngit log --oneline -5"},
        {"name": "Find Files", "code": "find . -name '*.py' -type f"},
    ],
    "Regex": [
        {"name": "Email", "code": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"},
        {"name": "Phone RU", "code": r"\+7[0-9]{10}"},
        {"name": "URL", "code": r"https?://[^\s/$.?#].[^\s]*"},
    ],
}


class SnippetsPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.data = {}
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
        add_cat_row.addWidget(self.new_cat)
        add_cat_btn = QPushButton("+")
        add_cat_btn.setFixedWidth(40)
        add_cat_btn.setToolTip("Add new category")
        add_cat_btn.clicked.connect(self._add_category)
        add_cat_row.addWidget(add_cat_btn)
        ll.addLayout(add_cat_row)

        right, inner_right, rl = self.card(tr("snippet_snippets_card"))
        outer.addWidget(right, 1)

        self.snip_list = QListWidget()
        self.snip_list.itemClicked.connect(self._show_code)
        rl.addWidget(self.snip_list)

        rl.addWidget(QLabel(tr("snippet_name_label")))
        self.snip_name = QLineEdit()
        self.snip_name.setPlaceholderText("Snippet name")
        rl.addWidget(self.snip_name)

        rl.addWidget(QLabel(tr("snippet_code_label")))
        self.snip_code = QPlainTextEdit()
        self.snip_code.setPlaceholderText("Paste code here...")
        self.snip_code.setObjectName("code_editor")
        rl.addWidget(self.snip_code, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for txt, fn, obj in [("+ " + tr("snippet_add"), self._add_snippet, "accent"),
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

    def _load(self):
        try:
            with open(SNIPPETS_FILE, encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = dict(DEFAULT_SNIPPETS)
            self._save()
        self._refresh_cats()

    def _save(self):
        try:
            with open(SNIPPETS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _refresh_cats(self):
        self.cat_list.clear()
        for cat in self.data:
            self.cat_list.addItem(cat)

    def _show_snippets(self, item):
        self.snip_list.clear()
        self.current_cat = item.text()
        for snip in self.data.get(self.current_cat, []):
            self.snip_list.addItem(snip["name"])

    def _show_code(self, item):
        snips = self.data.get(self.current_cat, [])
        for s in snips:
            if s["name"] == item.text():
                self.snip_name.setText(s["name"])
                self.snip_code.setPlainText(s["code"])
                break

    def _add_category(self):
        name = self.new_cat.text().strip()
        if name and name not in self.data:
            self.data[name] = []
            self._refresh_cats()
            self.new_cat.clear()
            self._save()

    def _add_snippet(self):
        tr = self.app.i18n.tr
        if not hasattr(self, "current_cat") or not self.current_cat:
            QMessageBox.warning(self, tr("snippet_error"), tr("snippet_select_category"))
            return
        name = self.snip_name.text().strip()
        code = self.snip_code.toPlainText()
        if not name:
            QMessageBox.warning(self, tr("snippet_error"), tr("snippet_enter_name"))
            return
        self.data[self.current_cat].append({"name": name, "code": code})
        self._show_snippets(self.cat_list.currentItem())
        self._save()

    def _del_snippet(self):
        item = self.snip_list.currentItem()
        if not item or not hasattr(self, "current_cat"):
            return
        self.data[self.current_cat] = [s for s in self.data[self.current_cat] if s["name"] != item.text()]
        self._show_snippets(self.cat_list.currentItem())
        self._save()

    def _copy_code(self):
        code = self.snip_code.toPlainText()
        if code:
            QApplication.clipboard().setText(code)
