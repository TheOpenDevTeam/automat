import json, random, string, uuid, ipaddress
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config import ACCENT, ACCENT2, GREEN
from ui.page_base import PageWidget
from core.activity_log import log, EVENT_DATAGEN, STATUS_OK

FIRST_NAMES_RU = ["\u0410\u043b\u0435\u043a\u0441\u0435\u0439","\u0414\u043c\u0438\u0442\u0440\u0438\u0439","\u041c\u0430\u0440\u0438\u044f","\u0415\u043b\u0435\u043d\u0430","\u0410\u043d\u043d\u0430","\u0421\u0435\u0440\u0433\u0435\u0439","\u041e\u043b\u044c\u0433\u0430","\u0410\u043d\u0434\u0440\u0435\u0439","\u041d\u0430\u0442\u0430\u043b\u044c\u044f","\u0418\u0432\u0430\u043d"]
LAST_NAMES_RU = ["\u0418\u0432\u0430\u043d\u043e\u0432","\u041f\u0435\u0442\u0440\u043e\u0432","\u0421\u0438\u0434\u043e\u0440\u043e\u0432","\u0421\u043c\u0438\u0440\u043d\u043e\u0432","\u041a\u0443\u0437\u043d\u0435\u0446\u043e\u0432","\u041f\u043e\u043f\u043e\u0432","\u0412\u0430\u0441\u0438\u043b\u044c\u0435\u0432","\u0417\u0430\u0439\u0446\u0435\u0432","\u041f\u0430\u0432\u043b\u043e\u0432","\u0421\u043e\u043a\u043e\u043b\u043e\u0432"]
CITIES_RU = ["\u041c\u043e\u0441\u043a\u0432\u0430","\u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433","\u041d\u043e\u0432\u043e\u0441\u0438\u0431\u0438\u0440\u0441\u043a","\u0415\u043a\u0430\u0442\u0435\u0440\u0438\u043d\u0431\u0443\u0440\u0433","\u041a\u0430\u0437\u0430\u043d\u044c","\u041a\u0440\u0430\u0441\u043d\u043e\u044f\u0440\u0441\u043a","\u041d\u0438\u0436\u043d\u0438\u0439 \u041d\u043e\u0432\u0433\u043e\u0440\u043e\u0434","\u0427\u0435\u043b\u044f\u0431\u0438\u043d\u0441\u043a","\u0423\u0444\u0430","\u0421\u0430\u043c\u0430\u0440\u0430"]
FIRST_NAMES_EN = ["James","John","Robert","Michael","David","Mary","Patricia","Jennifer","Linda","Barbara"]
LAST_NAMES_EN = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez"]
CITIES_EN = ["New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia","San Antonio","San Diego","Dallas","Austin"]

FIELD_TYPES = ["id", "name", "email", "phone", "age", "city", "company", "salary", "uuid", "ipv4", "active", "date", "text"]


class DataGenPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.tr = self.app.i18n.tr
        self.build()

    def build(self):
        tr = self.tr
        self.header("datagen", tr("datagen_title"), tr("datagen_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("datagen_params"))
        outer.addWidget(left)
        ll.addWidget(QLabel(tr("datagen_count")))
        self.count = QSpinBox(); self.count.setRange(1, 100000); self.count.setValue(10)
        ll.addWidget(self.count)
        ll.addWidget(QLabel(tr("datagen_format")))
        self.fmt = QComboBox(); self.fmt.addItems(["JSON", "CSV", "SQL", "XML", "Python List"])
        ll.addWidget(self.fmt)
        ll.addWidget(QLabel(tr("datagen_locale")))
        self.locale = QComboBox(); self.locale.addItems([tr("datagen_locale_ru"), tr("datagen_locale_en")])
        ll.addWidget(self.locale)
        ll.addWidget(QLabel(tr("datagen_fields")))
        self.fields = {}
        for f in FIELD_TYPES:
            cb = QCheckBox(f); cb.setChecked(True); self.fields[f] = cb; ll.addWidget(cb)
        gen_btn = QPushButton(tr("datagen_generate"))
        gen_btn.setObjectName("accent")
        gen_btn.clicked.connect(self._generate)
        ll.addWidget(gen_btn)
        save_btn = QPushButton(tr("datagen_save"))
        save_btn.clicked.connect(self._save)
        ll.addWidget(save_btn)

        right, inner_right, rl = self.card(tr("datagen_result"))
        outer.addWidget(right, 1)
        self.output = QPlainTextEdit()
        self.output.setObjectName("code_output")
        self.output.setReadOnly(True)
        rl.addWidget(self.output)

    def _gen_value(self, field, i, is_ru):
        first = FIRST_NAMES_RU if is_ru else FIRST_NAMES_EN
        last = LAST_NAMES_RU if is_ru else LAST_NAMES_EN
        cities = CITIES_RU if is_ru else CITIES_EN
        if field == "id": return i
        if field == "name": return f"{random.choice(first)} {random.choice(last)}"
        if field == "email": return f"{random.choice(first).lower()}.{random.choice(last).lower()}{random.randint(1,999)}@example.com"
        if field == "phone": return f"+7{random.randint(900,999)}{random.randint(1000000,9999999)}"
        if field == "age": return random.randint(18, 70)
        if field == "city": return random.choice(cities)
        if field == "company": return f"Company {random.choice(string.ascii_uppercase)}"
        if field == "salary": return random.randint(30000, 200000)
        if field == "uuid": return str(uuid.uuid4())
        if field == "ipv4": return str(ipaddress.IPv4Address(random.randint(0, 2**32 - 1)))
        if field == "active": return random.choice([True, False])
        if field == "date": return (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 2000))).strftime("%Y-%m-%d")
        if field == "text": return " ".join(random.choice(["lorem","ipsum","dolor","sit","amet","consectetur","adipiscing","elit","sed","do","eiusmod","tempor","incididunt","ut","labore","et","dolore"]) for _ in range(random.randint(5, 15)))
        return None

    def _generate(self):
        tr = self.tr
        n = self.count.value()
        is_ru = self.locale.currentText() == tr("datagen_locale_ru")
        active_fields = [f for f, cb in self.fields.items() if cb.isChecked()]
        if not active_fields:
            QMessageBox.warning(self, tr("datagen_error"), tr("datagen_select_field"))
            return

        data = []
        for i in range(1, n + 1):
            row = {}
            for f in active_fields:
                v = self._gen_value(f, i, is_ru)
                if v is not None:
                    row[f] = v
            data.append(row)

        fmt = self.fmt.currentText()
        if fmt == "JSON":
            text = json.dumps(data, ensure_ascii=False, indent=2)
        elif fmt == "CSV":
            if data:
                text = ",".join(data[0].keys()) + "\n"
                text += "\n".join(",".join(str(v) for v in r.values()) for r in data)
            else: text = ""
        elif fmt == "SQL":
            if data:
                cols = ",".join(data[0].keys())
                text = f"CREATE TABLE generated ({','.join(f'{k} TEXT' for k in data[0].keys())});\n"
                text += "\n".join(f"INSERT INTO generated ({cols}) VALUES ({','.join(repr(str(v)) for v in r.values())});" for r in data)
            else: text = ""
        elif fmt == "XML":
            text = "<data>\n"
            for r in data:
                text += "  <record>\n"
                for k, v in r.items():
                    text += f"    <{k}>{v}</{k}>\n"
                text += "  </record>\n"
            text += "</data>"
        else:
            text = str(data)

        self.output.setPlainText(text)
        log(EVENT_DATAGEN, STATUS_OK, f"{n} \u0437\u0430\u043f\u0438\u0441\u0435\u0439", n)

    def _save(self):
        tr = self.tr
        fp, _ = QFileDialog.getSaveFileName(self, tr("datagen_save_dialog"), "", tr("datagen_save_all_files"))
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.output.toPlainText())
            QMessageBox.information(self, tr("datagen_saved"), f"\u2713 {fp}")
