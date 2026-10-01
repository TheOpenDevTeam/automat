"""
Extra tools: QR generator, screen color picker, curl → code converter.
qrcode is optional (pip install qrcode); everything else is stdlib + Qt.
"""

import io
import shlex
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.ui.page_base import PageWidget

try:
    import qrcode as _qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False


# ── curl parsing (pure logic, testable) ──────────────────────────────────────

def parse_curl(cmd):
    """Parse curl command into dict: method, url, headers, data, user."""
    try:
        parts = shlex.split(cmd, posix=True)
    except ValueError:
        parts = cmd.split()
    # drop leading 'curl'
    if parts and parts[0].lower() == "curl":
        parts = parts[1:]
    method, url, headers, data, user = "GET", "", {}, None, None
    i = 0
    while i < len(parts):
        p = parts[i]
        nxt = parts[i + 1] if i + 1 < len(parts) else ""
        if p in ("-X", "--request"):
            method, i = nxt.upper(), i + 2
        elif p in ("-H", "--header"):
            if ":" in nxt:
                k, v = nxt.split(":", 1)
                headers[k.strip()] = v.strip()
            i += 2
        elif p in ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii"):
            data, i = nxt, i + 2
        elif p in ("-u", "--user"):
            user, i = nxt, i + 2
        elif p in ("--compressed", "--silent", "-s", "-i", "--include", "-v", "--verbose",
                   "-L", "--location", "-k", "--insecure"):
            i += 1
        elif p.startswith("-"):
            # unknown flag: skip value if it doesn't look like a flag
            if nxt and not nxt.startswith("-") and p not in ("-o", "--output"):
                i += 2
            else:
                i += 1
        else:
            if not url and (p.startswith("http") or "." in p):
                url = p if p.startswith("http") else "http://" + p
            i += 1
    if data and method == "GET":
        method = "POST"
    return {"method": method, "url": url, "headers": headers, "data": data, "user": user}


def to_requests(spec):
    lines = ["import requests", ""]
    if spec["headers"]:
        lines.append(f"headers = {spec['headers']!r}")
    if spec["data"]:
        lines.append(f"data = {spec['data']!r}")
    args = [f"'{spec['url']}'"]
    if spec["headers"]:
        args.append("headers=headers")
    if spec["data"]:
        # try json payload
        args.append("data=data")
    if spec["user"]:
        args.append(f"auth=tuple({spec['user']!r}.split(':', 1))")
    args.append("timeout=15")
    lines.append("")
    lines.append(f"r = requests.{spec['method'].lower()}({', '.join(args)})")
    lines.append("r.raise_for_status()")
    lines.append("print(r.text)")
    return "\n".join(lines)


def to_fetch(spec):
    import json as _json
    opts = {"method": spec["method"]}
    if spec["headers"]:
        opts["headers"] = spec["headers"]
    if spec["data"]:
        opts["body"] = spec["data"]
    return (f"const r = await fetch('{spec['url']}', {_json.dumps(opts, indent=2)});\n"
            f"const text = await r.text();\nconsole.log(text);")


def to_httpie(spec):
    parts = ["http", spec["method"], spec["url"]]
    for k, v in spec["headers"].items():
        parts.append(f"'{k}:{v}'")
    if spec["data"]:
        parts.append(f"'{spec['data']}'")
    if spec["user"]:
        parts.append(f"-a {spec['user']}")
    return " ".join(parts)


# ── page ─────────────────────────────────────────────────────────────────────

class ExtraToolsPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.tr = self.app.i18n.tr
        self._colors = []
        self._picking = False
        self.build()

    def build(self):
        tr = self.tr
        self.header("tools", tr("xt_title"), tr("xt_subtitle"))
        tabs = QTabWidget()
        self.content_layout.addWidget(tabs, 1)
        tabs.addTab(self._qr_tab(), tr("xt_tab_qr"))
        tabs.addTab(self._palette_tab(), tr("xt_tab_palette"))
        tabs.addTab(self._curl_tab(), tr("xt_tab_curl"))

    # ── QR ──
    def _qr_tab(self):
        tr = self.tr
        w = QWidget()
        lay = QHBoxLayout(w)
        left, _, ll = self.card(tr("xt_qr_params"))
        lay.addWidget(left)
        ll.addWidget(QLabel(tr("xt_qr_text")))
        self.qr_input = QPlainTextEdit()
        self.qr_input.setMaximumHeight(100)
        self.qr_input.setPlaceholderText("https://example.com")
        ll.addWidget(self.qr_input)
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel(tr("xt_qr_size")))
        self.qr_size = QSpinBox()
        self.qr_size.setRange(4, 40)
        self.qr_size.setValue(10)
        size_row.addWidget(self.qr_size, 1)
        ll.addLayout(size_row)
        gen_btn = QPushButton(tr("xt_qr_generate"))
        gen_btn.setObjectName("accent")
        gen_btn.clicked.connect(self._gen_qr)
        ll.addWidget(gen_btn)
        save_btn = QPushButton(tr("xt_qr_save"))
        save_btn.clicked.connect(self._save_qr)
        ll.addWidget(save_btn)
        self.qr_hint = QLabel("" if HAS_QRCODE else tr("xt_qr_need"))
        self.qr_hint.setObjectName("text_muted")
        self.qr_hint.setWordWrap(True)
        ll.addWidget(self.qr_hint)

        right, _, rl = self.card(tr("xt_qr_preview"))
        lay.addWidget(right, 1)
        self.qr_view = QLabel()
        self.qr_view.setAlignment(Qt.AlignCenter)
        self.qr_view.setMinimumSize(280, 280)
        rl.addWidget(self.qr_view, 1)
        self._qr_bytes = None
        return w

    def _gen_qr(self):
        tr = self.tr
        if not HAS_QRCODE:
            QMessageBox.warning(self, tr("xt_error"), tr("xt_qr_need"))
            return
        text = self.qr_input.toPlainText().strip()
        if not text:
            return
        try:
            qr = _qrcode.QRCode(box_size=self.qr_size.value(), border=4)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self._qr_bytes = buf.getvalue()
            qimg = QImage.fromData(self._qr_bytes)
            pm = QPixmap.fromImage(qimg).scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.qr_view.setPixmap(pm)
        except Exception as e:
            QMessageBox.warning(self, tr("xt_error"), str(e))

    def _save_qr(self):
        tr = self.tr
        if not self._qr_bytes:
            return
        fp, _ = QFileDialog.getSaveFileName(self, tr("xt_qr_save"), "qr.png", "PNG (*.png)")
        if fp:
            with open(fp, "wb") as f:
                f.write(self._qr_bytes)
            QMessageBox.information(self, tr("xt_saved"), f"✓ {fp}")

    # ── palette ──
    def _palette_tab(self):
        tr = self.tr
        w = QWidget()
        lay = QHBoxLayout(w)
        left, _, ll = self.card(tr("xt_pal_pick"))
        lay.addWidget(left)
        pick_btn = QPushButton(tr("xt_pal_pick_btn"))
        pick_btn.setObjectName("accent")
        pick_btn.setCheckable(True)
        pick_btn.clicked.connect(self._toggle_pick)
        ll.addWidget(pick_btn)
        ll.addWidget(QLabel(tr("xt_pal_hex")))
        hex_row = QHBoxLayout()
        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("#4f8ef7")
        self.hex_input.returnPressed.connect(self._hex_entered)
        hex_row.addWidget(self.hex_input, 1)
        ll.addLayout(hex_row)
        self.swatch = QLabel()
        self.swatch.setFixedHeight(60)
        self.swatch.setObjectName("code_output")
        ll.addWidget(self.swatch)
        self.rgb_lbl = QLabel("—")
        ll.addWidget(self.rgb_lbl)
        self.hsl_lbl = QLabel("—")
        self.hsl_lbl.setObjectName("text_muted")
        ll.addWidget(self.hsl_lbl)
        copy_btn = QPushButton(tr("xt_pal_copy"))
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.hex_input.text()))
        ll.addWidget(copy_btn)

        right, _, rl = self.card(tr("xt_pal_history"))
        lay.addWidget(right, 1)
        self.color_list = QListWidget()
        self.color_list.itemClicked.connect(self._color_clicked)
        rl.addWidget(self.color_list, 1)
        clear_btn = QPushButton(tr("xt_pal_clear"))
        clear_btn.clicked.connect(lambda: (self._colors.clear(), self.color_list.clear()))
        rl.addWidget(clear_btn)
        return w

    def _toggle_pick(self, on):
        tr = self.tr
        self._picking = on
        if on:
            QApplication.setOverrideCursor(Qt.CrossCursor)
            self._pick_timer = QTimer(self)
            self._pick_timer.timeout.connect(self._grab_pixel)
            self._pick_timer.start(80)
        else:
            QApplication.restoreOverrideCursor()
            if hasattr(self, "_pick_timer"):
                self._pick_timer.stop()

    def _grab_pixel(self):
        if not self._picking:
            return
        pos = QCursor.pos()
        screen = QApplication.primaryScreen()
        if not screen:
            return
        pm = screen.grabWindow(0, pos.x(), pos.y(), 1, 1)
        c = QColor(pm.toImage().pixel(0, 0))
        self._show_color(c)
        # click to lock: left button pressed
        if QApplication.mouseButtons() & Qt.LeftButton:
            for b in self.findChildren(QPushButton):
                if b.isCheckable() and b.isChecked():
                    b.setChecked(False)
            self._toggle_pick(False)
            self._push_color(c)

    def _hex_entered(self):
        txt = self.hex_input.text().strip()
        if not txt.startswith("#"):
            txt = "#" + txt
        c = QColor(txt)
        if c.isValid():
            self._show_color(c)
            self._push_color(c)

    def _show_color(self, c):
        self.hex_input.setText(c.name())
        self.swatch.setStyleSheet(f"background: {c.name()}; border-radius: 4px;")
        self.rgb_lbl.setText(f"RGB({c.red()}, {c.green()}, {c.blue()})")
        h, s, l, _ = c.getHsl()
        self.hsl_lbl.setText(f"HSL({h}, {s}, {l})")

    def _push_color(self, c):
        hx = c.name()
        if hx not in self._colors:
            self._colors.insert(0, hx)
            self._colors = self._colors[:20]
            self._rebuild_colors()

    def _rebuild_colors(self):
        self.color_list.clear()
        for hx in self._colors:
            item = QListWidgetItem(f"⬛ {hx}")
            item.setData(Qt.UserRole, hx)
            c = QColor(hx)
            item.setForeground(QBrush(c.lightness() > 128 and QColor("#222") or QColor("#eee")))
            item.setBackground(QBrush(c))
            self.color_list.addItem(item)

    def _color_clicked(self, item):
        hx = item.data(Qt.UserRole)
        if hx:
            QApplication.clipboard().setText(hx)
            self.hex_input.setText(hx)
            self._show_color(QColor(hx))

    # ── curl ──
    def _curl_tab(self):
        tr = self.tr
        w = QWidget()
        lay = QVBoxLayout(w)
        top, _, tl = self.card(tr("xt_curl_input"))
        lay.addWidget(top)
        self.curl_input = QPlainTextEdit()
        self.curl_input.setMaximumHeight(120)
        self.curl_input.setPlaceholderText("curl -X POST 'https://api.example.com' -H 'Content-Type: application/json' -d '{\"k\": 1}'")
        self.curl_input.setObjectName("code_editor")
        tl.addWidget(self.curl_input)
        row = QHBoxLayout()
        row.addWidget(QLabel(tr("xt_curl_target")))
        self.curl_target = QComboBox()
        self.curl_target.addItems(["Python requests", "JavaScript fetch", "HTTPie"])
        row.addWidget(self.curl_target, 1)
        conv_btn = QPushButton(tr("xt_curl_convert"))
        conv_btn.setObjectName("accent")
        conv_btn.clicked.connect(self._convert_curl)
        row.addWidget(conv_btn)
        tl.addLayout(row)
        bot, _, bl = self.card(tr("xt_curl_output"))
        lay.addWidget(bot, 1)
        self.curl_output = QPlainTextEdit()
        self.curl_output.setReadOnly(True)
        self.curl_output.setObjectName("code_output")
        bl.addWidget(self.curl_output, 1)
        copy_btn = QPushButton(tr("xt_pal_copy"))
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.curl_output.toPlainText()))
        bl.addWidget(copy_btn)
        return w

    def _convert_curl(self):
        tr = self.tr
        raw = self.curl_input.toPlainText().strip()
        if not raw:
            return
        try:
            spec = parse_curl(raw)
            if not spec["url"]:
                self.curl_output.setPlainText(tr("xt_curl_no_url"))
                return
            idx = self.curl_target.currentIndex()
            if idx == 0:
                out = to_requests(spec)
            elif idx == 1:
                out = to_fetch(spec)
            else:
                out = to_httpie(spec)
            self.curl_output.setPlainText(out)
        except Exception as e:
            self.curl_output.setPlainText(f"Error: {e}")
