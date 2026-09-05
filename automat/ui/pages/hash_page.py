import hashlib, base64, urllib.parse, hmac, os, threading
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config import ACCENT, GREEN, YELLOW, RED
from ui.page_base import PageWidget
from core.activity_log import log, EVENT_HASH, STATUS_OK
from util import safe


class HashPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.build()

    def build(self):
        tr = self.app.i18n.tr
        self.header("hash", tr("hash_title"), tr("hash_subtitle"))

        tabs = QTabWidget()
        self.content_layout.addWidget(tabs)

        self._build_hash(tabs)
        self._build_hmac(tabs)
        self._build_filehash(tabs)
        self._build_b64(tabs)
        self._build_url(tabs)

    def _build_hash(self, tabs):
        tr = self.app.i18n.tr
        c1, i1, l1 = self.card(tr("hash_text_card"))
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText(tr("hash_text_placeholder"))
        l1.addWidget(self.hash_input)
        self.hash_algo = QComboBox()
        self.hash_algo.addItems(["md5", "sha1", "sha256", "sha512", "sha3_256", "blake2b", "blake2s"])
        l1.addWidget(self.hash_algo)
        calc_btn = QPushButton(tr("hash_calc_hash"))
        calc_btn.setObjectName("accent")
        calc_btn.setToolTip("Compute hash")
        calc_btn.clicked.connect(self._calc)
        l1.addWidget(calc_btn)
        row = QHBoxLayout()
        self.hash_result = QLineEdit()
        self.hash_result.setPlaceholderText("Result will appear here")
        self.hash_result.setReadOnly(True)
        row.addWidget(self.hash_result, 1)
        copy_btn = QPushButton(tr("hash_copy"))
        copy_btn.setToolTip("Copy to clipboard")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.hash_result.text()))
        row.addWidget(copy_btn)
        l1.addLayout(row)
        tabs.addTab(c1, tr("hash_tab_hash"))

    def _build_hmac(self, tabs):
        tr = self.app.i18n.tr
        c, i, l = self.card("HMAC-SHA256")
        l.addWidget(QLabel(tr("hash_hmac_key")))
        self.hmac_key = QLineEdit()
        self.hmac_key.setPlaceholderText(tr("hash_hmac_key_placeholder"))
        l.addWidget(self.hmac_key)
        l.addWidget(QLabel(tr("hash_hmac_msg")))
        self.hmac_msg = QLineEdit()
        self.hmac_msg.setPlaceholderText(tr("hash_hmac_msg_placeholder"))
        l.addWidget(self.hmac_msg)
        calc_btn = QPushButton(tr("hash_hmac_calc"))
        calc_btn.setObjectName("accent")
        calc_btn.setToolTip("Compute HMAC")
        calc_btn.clicked.connect(self._calc_hmac)
        l.addWidget(calc_btn)
        self.hmac_result = QLineEdit()
        self.hmac_result.setPlaceholderText("Result will appear here")
        self.hmac_result.setReadOnly(True)
        l.addWidget(self.hmac_result)
        tabs.addTab(c, "HMAC")

    def _build_filehash(self, tabs):
        tr = self.app.i18n.tr
        c, i, l = self.card(tr("hash_file_card"))
        row = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText(tr("hash_file_placeholder"))
        row.addWidget(self.file_path, 1)
        browse_btn = QPushButton(tr("hash_file_browse"))
        browse_btn.clicked.connect(lambda: self.file_path.setText(QFileDialog.getOpenFileName(self, tr("hash_file_dialog"))[0]))
        row.addWidget(browse_btn)
        l.addLayout(row)
        self.file_algo = QComboBox()
        self.file_algo.addItems(["md5", "sha1", "sha256", "sha512"])
        l.addWidget(self.file_algo)
        calc_btn = QPushButton(tr("hash_file_calc"))
        calc_btn.setObjectName("accent")
        calc_btn.setToolTip("Compute file hash")
        calc_btn.clicked.connect(self._calc_file)
        l.addWidget(calc_btn)
        self.file_result = QLineEdit()
        self.file_result.setPlaceholderText("Result will appear here")
        self.file_result.setReadOnly(True)
        l.addWidget(self.file_result)
        self.file_progress = QProgressBar()
        self.file_progress.setVisible(False)
        self.file_progress.setFixedHeight(6)
        l.addWidget(self.file_progress)
        tabs.addTab(c, tr("hash_tab_file"))

    def _build_b64(self, tabs):
        tr = self.app.i18n.tr
        c, i, l = self.card("BASE64")
        self.b64_input = QLineEdit()
        self.b64_input.setPlaceholderText(tr("hash_b64_placeholder"))
        l.addWidget(self.b64_input)
        row = QHBoxLayout()
        enc_btn = QPushButton(tr("hash_b64_encode"))
        enc_btn.setObjectName("accent")
        enc_btn.setToolTip("Encode to Base64")
        enc_btn.clicked.connect(lambda: self._b64(True))
        dec_btn = QPushButton(tr("hash_b64_decode"))
        dec_btn.setObjectName("accent2")
        dec_btn.setToolTip("Decode from Base64")
        dec_btn.clicked.connect(lambda: self._b64(False))
        row.addWidget(enc_btn); row.addWidget(dec_btn)
        l.addLayout(row)
        self.b64_result = QLineEdit()
        self.b64_result.setPlaceholderText("Result will appear here")
        self.b64_result.setReadOnly(True)
        l.addWidget(self.b64_result)
        tabs.addTab(c, "Base64")

    def _build_url(self, tabs):
        tr = self.app.i18n.tr
        c, i, l = self.card("URL")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(tr("hash_url_placeholder"))
        l.addWidget(self.url_input)
        row = QHBoxLayout()
        enc_btn = QPushButton(tr("hash_url_encode"))
        enc_btn.setObjectName("accent")
        enc_btn.setToolTip("URL encode")
        enc_btn.clicked.connect(lambda: self._url(True))
        dec_btn = QPushButton(tr("hash_url_decode"))
        dec_btn.setObjectName("accent2")
        dec_btn.setToolTip("URL decode")
        dec_btn.clicked.connect(lambda: self._url(False))
        row.addWidget(enc_btn); row.addWidget(dec_btn)
        l.addLayout(row)
        self.url_result = QLineEdit()
        self.url_result.setPlaceholderText("Result will appear here")
        self.url_result.setReadOnly(True)
        l.addWidget(self.url_result)
        tabs.addTab(c, "URL")

    def _calc(self):
        text = self.hash_input.text()
        if not text:
            return
        algo = self.hash_algo.currentText()
        try:
            h = hashlib.new(algo, text.encode()).hexdigest()
            self.hash_result.setText(h)
            log(EVENT_HASH, STATUS_OK, algo, 1)
        except Exception as e:
            self.hash_result.setText(str(e))

    def _calc_hmac(self):
        key = self.hmac_key.text()
        msg = self.hmac_msg.text()
        if not key or not msg:
            return
        h = hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()
        self.hmac_result.setText(h)

    def _calc_file(self):
        path = self.file_path.text()
        if not os.path.isfile(path):
            QMessageBox.warning(self, "\u041e\u0448\u0438\u0431\u043a\u0430", "\u0424\u0430\u0439\u043b \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d")
            return
        threading.Thread(target=self._hash_file, daemon=True).start()

    def _hash_file(self):
        path = self.file_path.text()
        algo = self.file_algo.currentText()
        try:
            size = os.path.getsize(path)
        except Exception as e:
            safe(self.file_result.setText, str(e))
            return
        safe(self.file_progress.setVisible, True)
        safe(self.file_progress.setValue, 0)
        try:
            h = hashlib.new(algo)
            with open(path, "rb") as f:
                processed = 0
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    h.update(chunk)
                    processed += len(chunk)
                    if size > 0:
                        safe(self.file_progress.setValue, int(processed / size * 100))
            safe(self.file_result.setText, h.hexdigest())
            safe(self.file_progress.setValue, 100)
            log(EVENT_HASH, STATUS_OK, f"file {algo}", 1)
        except Exception as e:
            safe(self.file_result.setText, str(e))
        safe(self.file_progress.setVisible, False)

    def _b64(self, encode):
        text = self.b64_input.text()
        if not text:
            return
        try:
            if encode:
                self.b64_result.setText(base64.b64encode(text.encode()).decode())
            else:
                self.b64_result.setText(base64.b64decode(text).decode())
        except Exception as e:
            self.b64_result.setText(str(e))

    def _url(self, encode):
        text = self.url_input.text()
        if not text:
            return
        try:
            if encode:
                self.url_result.setText(urllib.parse.quote(text))
            else:
                self.url_result.setText(urllib.parse.unquote(text))
        except Exception as e:
            self.url_result.setText(str(e))
