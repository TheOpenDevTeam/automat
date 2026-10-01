"""
API Client page — REST client, JSON/YAML/XML formatter with validation,
pretty-printing, minification, and JSONPath queries.
"""

import json
import re

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from automat.config import GREEN, YELLOW, RED
from automat.ui.page_base import PageWidget
from automat.core.worker import run_in_background

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

import xml.etree.ElementTree as ET
from xml.dom import minidom


class ApiToolsPage(PageWidget):
    """REST API client with built-in JSON, YAML and XML formatting tools."""

    def __init__(self, app):
        super().__init__(app)
        self.build()

    def build(self):
        tr = self.app.i18n.tr
        self.header("api", tr("api_title"), tr("api_subtitle"))

        tabs = QTabWidget()
        self.content_layout.addWidget(tabs)
        self._build_rest(tabs)
        self._build_formatter(tabs)

    def _build_rest(self, tabs):
        tr = self.app.i18n.tr
        w = QWidget()
        l = QVBoxLayout(w)

        url_row = QHBoxLayout()
        self.method = QComboBox()
        self.method.addItems(["GET", "POST", "PUT", "PATCH", "DELETE"])
        self.method.setFixedWidth(100)
        url_row.addWidget(self.method)

        self.url = QLineEdit()
        self.url.setPlaceholderText("https://api.example.com/endpoint")
        url_row.addWidget(self.url, 1)
        send_btn = QPushButton(tr("api_send"))
        send_btn.setObjectName("accent")
        send_btn.clicked.connect(self._send_request)
        url_row.addWidget(send_btn)
        l.addLayout(url_row)

        l.addWidget(QLabel(tr("api_headers")))
        self.headers_input = QPlainTextEdit()
        self.headers_input.setPlaceholderText('{"Authorization": "Bearer token"}')
        self.headers_input.setMaximumHeight(80)
        l.addWidget(self.headers_input)

        l.addWidget(QLabel(tr("api_body")))
        self.body_input = QPlainTextEdit()
        self.body_input.setPlaceholderText('{"key": "value"}')
        self.body_input.setMaximumHeight(120)
        l.addWidget(self.body_input)

        l.addWidget(QLabel(tr("api_response")))
        self.response = QPlainTextEdit()
        self.response.setObjectName("api_response")
        self.response.setReadOnly(True)
        l.addWidget(self.response, 1)

        self.status_lbl = QLabel(tr("api_ready"))
        self.status_lbl.setObjectName("api_status")
        l.addWidget(self.status_lbl)

        tabs.addTab(w, tr("api_rest_tab"))

    def _set_api_status(self, text, color):
        self.status_lbl.setText(text)
        self.status_lbl.setProperty("status_color", color)
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

    def _send_request(self):
        if not HAS_REQUESTS:
            QMessageBox.warning(self, "Error", self.app.i18n.tr("api_no_requests"))
            return
        method = self.method.currentText().lower()
        url = self.url.text()
        try:
            headers = json.loads(self.headers_input.toPlainText()) if self.headers_input.toPlainText() else {}
        except Exception:
            headers = {}
        try:
            body = json.loads(self.body_input.toPlainText()) if self.body_input.toPlainText() else None
        except Exception:
            body = self.body_input.toPlainText()

        self.status_lbl.setText("Sending...")
        self.status_lbl.setProperty("status_color", YELLOW)
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

        run_in_background(
            self._do_request_bg, method, url, headers, body,
            on_result=self._on_request_done,
            on_error=lambda e: self._on_request_error(str(e)),
        )

    def _do_request_bg(self, method, url, headers, body):
        r = requests.request(method, url, json=body, headers=headers, timeout=30)
        return {
            "text": r.text,
            "status_code": r.status_code,
            "reason": r.reason,
            "content_len": len(r.content),
            "ok": r.ok,
        }

    def _on_request_done(self, result):
        raw = result["text"]
        if raw[:1] in ("{", "["):
            try:
                raw = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
            except Exception:
                pass
        self.response.setPlainText(raw)
        color = GREEN if result["ok"] else RED
        self._set_api_status(
            f"{result['status_code']} {result['reason']} ({result['content_len']} bytes)",
            color)

    def _on_request_error(self, error):
        self.response.setPlainText(error)
        self._set_api_status(f"Error: {error}", RED)

    def _build_formatter(self, tabs):
        tr = self.app.i18n.tr
        w = QWidget()
        l = QVBoxLayout(w)

        controls = QHBoxLayout()
        controls.addWidget(QLabel(tr("api_format")))
        self.format_combo = QComboBox()
        self.format_combo.addItems([tr("api_auto_detect"), "JSON", "YAML", "XML"])
        controls.addWidget(self.format_combo)

        controls.addSpacing(16)
        for label, obj, slot in [
            (tr("api_validate"), "accent", self._validate),
            (tr("api_pretty"), None, self._pretty),
            (tr("api_minify"), None, self._minify),
        ]:
            btn = QPushButton(label)
            if obj:
                btn.setObjectName(obj)
            btn.clicked.connect(slot)
            controls.addWidget(btn)

        l.addLayout(controls)

        l.addWidget(QLabel(tr("api_input")))
        self.fmt_input = QPlainTextEdit()
        self.fmt_input.setObjectName("fmt_editor")
        self.fmt_input.setPlaceholderText(
            'Paste JSON, YAML, or XML content here...\n\n'
            'Example JSON:\n{"users": [{"name": "Alice", "age": 30}]}\n\n'
            'Example YAML:\nusers:\n  - name: Alice\n    age: 30\n\n'
            'Example XML:\n<users><user><name>Alice</name><age>30</age></user></users>'
        )
        l.addWidget(self.fmt_input, 1)

        self.fmt_status = QLabel("")
        self.fmt_status.setObjectName("fmt_status")
        l.addWidget(self.fmt_status)

        l.addWidget(QLabel(tr("api_output")))
        self.fmt_output = QPlainTextEdit()
        self.fmt_output.setObjectName("fmt_editor")
        self.fmt_output.setReadOnly(True)
        l.addWidget(self.fmt_output, 1)

        tabs.addTab(w, tr("api_formatter_tab"))

    def _set_fmt_status(self, text, color):
        self.fmt_status.setText(text)
        self.fmt_status.setProperty("status_color", color)
        self.fmt_status.style().unpolish(self.fmt_status)
        self.fmt_status.style().polish(self.fmt_status)

    def _detect_format(self, text):

        stripped = text.strip()
        if not stripped:
            return None
        if stripped.startswith("<"):
            return "xml"
        if stripped[0] in ("{", "["):
            try:
                json.loads(stripped)
                return "json"
            except Exception:
                pass
        if HAS_YAML:
            try:
                yaml.safe_load(stripped)
                return "yaml"
            except Exception:
                pass
        return None

    def _get_format(self):

        choice = self.format_combo.currentText()
        if choice == "Auto-detect":
            text = self.fmt_input.toPlainText()
            return self._detect_format(text)
        return choice.lower()

    def _validate(self):
        text = self.fmt_input.toPlainText()
        fmt = self._get_format()
        if not text.strip():
            self._set_fmt_status("Nothing to validate.", YELLOW)
            self.fmt_output.clear()
            return
        try:
            if fmt == "json":
                json.loads(text)
                self._set_fmt_status("Valid JSON", GREEN)
                self.fmt_output.clear()
            elif fmt == "yaml":
                if HAS_YAML:
                    yaml.safe_load(text)
                    self._set_fmt_status("Valid YAML", GREEN)
                    self.fmt_output.clear()
                else:
                    self._set_fmt_status("YAML support requires PyYAML: pip install pyyaml", YELLOW)
            elif fmt == "xml":
                ET.fromstring(text)
                self._set_fmt_status("Valid XML", GREEN)
                self.fmt_output.clear()
            else:
                self._set_fmt_status("Could not detect format. Try selecting it manually.", YELLOW)
        except Exception as e:
            self._set_fmt_status(f"Invalid: {e}", RED)

    def _pretty(self):
        text = self.fmt_input.toPlainText()
        fmt = self._get_format()
        if not text.strip():
            return
        try:
            if fmt == "json":
                data = json.loads(text)
                pretty = json.dumps(data, indent=2, ensure_ascii=False)
                self.fmt_output.setPlainText(pretty)
                self._set_fmt_status("Formatted successfully", GREEN)
            elif fmt == "yaml":
                if HAS_YAML:
                    data = yaml.safe_load(text)
                    pretty = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
                    self.fmt_output.setPlainText(pretty)
                    self._set_fmt_status("Formatted successfully", GREEN)
                else:
                    self.fmt_output.setPlainText(text)
                    self._set_fmt_status("YAML pretty-print requires PyYAML", YELLOW)
            elif fmt == "xml":
                dom = minidom.parseString(text)
                pretty = dom.toprettyxml(indent="  ")
                pretty = "\n".join(pretty.split("\n")[1:])
                self.fmt_output.setPlainText(pretty)
                self._set_fmt_status("Formatted successfully", GREEN)
            else:
                self._set_fmt_status("Could not detect format.", YELLOW)
        except Exception as e:
            self._set_fmt_status(f"Error: {e}", RED)

    def _minify(self):
        text = self.fmt_input.toPlainText()
        fmt = self._get_format()
        if not text.strip():
            return
        try:
            if fmt == "json":
                data = json.loads(text)
                compressed = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
                self.fmt_output.setPlainText(compressed)
                self._set_fmt_status(f"Minified ({len(text)} \u2192 {len(compressed)} chars)", GREEN)
            elif fmt == "yaml":
                if HAS_YAML:
                    data = yaml.safe_load(text)
                    compressed = yaml.dump(data, default_flow_style=True, allow_unicode=True)
                    self.fmt_output.setPlainText(compressed)
                    self._set_fmt_status("Minified (flow style)", GREEN)
                else:
                    self.fmt_output.setPlainText(text)
                    self._set_fmt_status("YAML minify requires PyYAML", YELLOW)
            elif fmt == "xml":
                dom = minidom.parseString(text)
                compressed = dom.toxml()
                self.fmt_output.setPlainText(compressed)
                self._set_fmt_status(f"Minified ({len(text)} \u2192 {len(compressed)} chars)", GREEN)
            else:
                self._set_fmt_status("Could not detect format.", YELLOW)
        except Exception as e:
            self._set_fmt_status(f"Error: {e}", RED)
