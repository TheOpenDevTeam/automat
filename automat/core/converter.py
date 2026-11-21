"""
Converter business logic — file conversion algorithms, dependency checks,
and progress reporting. No Qt dependencies; testable without QApplication.
"""

import csv
import os
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ConversionResult:
    ok: bool
    file: str
    output: Optional[str] = None
    error: Optional[str] = None


class Converter:
    """Handles file conversion business logic.

    Callbacks:
      on_progress(frac)  — 0.0..1.0 completion
      on_log(msg, tag)   — status log entry
      on_error(msg)      — non-fatal error for a single file
    """

    def __init__(self):
        self.stop_flag = False

    def stop(self):
        self.stop_flag = True

    # ------------------------------------------------------------------
    # Dependency checks
    # ------------------------------------------------------------------

    def _check(self, libs: tuple) -> bool:
        return all(libs)

    # ------------------------------------------------------------------
    # Conversion entry point
    # ------------------------------------------------------------------

    def convert_files(
        self,
        files: list[str],
        conv_type: str,
        output_dir: str,
        on_progress: Optional[Callable[[float], None]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> list[ConversionResult]:
        """Convert a list of files. Returns per-file results."""
        results: list[ConversionResult] = []
        total = len(files)

        for i, f in enumerate(files):
            if self.stop_flag:
                break

            if on_progress:
                on_progress((i + 1) / total * 100.0)

            name = os.path.basename(f)
            if on_log:
                on_log(f"[{i + 1}/{total}] {name}", "info")

            try:
                result = self._convert_one(f, conv_type, output_dir)
                results.append(result)
                if result.ok:
                    if on_log:
                        on_log(f"\u2713 {name}", "ok")
                else:
                    if on_error:
                        on_error(result.error or f"failed: {name}")
            except Exception as exc:  # noqa: BLE001
                results.append(ConversionResult(ok=False, file=name, error=str(exc)))
                if on_error:
                    on_error(f"{name}: {exc}")

        if on_progress:
            on_progress(100.0)
        return results

    # ------------------------------------------------------------------
    # Single-file conversion
    # ------------------------------------------------------------------

    def _convert_one(self, f: str, conv_type: str, output_dir: str) -> ConversionResult:
        ext = os.path.splitext(f)[1].lower()
        name = os.path.splitext(os.path.basename(f))[0]
        dst = os.path.join(output_dir, name)

        if "Excel \u2192 PDF" in conv_type and ext in (".xlsx", ".xls"):
            return self._excel_to_pdf(f, dst)
        if "PDF \u2192 Word" in conv_type and ext == ".pdf":
            return self._pdf_to_word(f, dst)
        if "Word \u2192 PDF" in conv_type and ext == ".docx":
            return self._word_to_pdf(f, dst)
        if "Images \u2192 PDF" in conv_type and ext in (".png", ".jpg", ".jpeg", ".bmp"):
            return self._images_to_pdf(f, dst)
        if "PDF \u2192 TXT" in conv_type and ext == ".pdf":
            return self._pdf_to_txt(f, dst)
        if "CSV \u2192 Excel" in conv_type and ext == ".csv":
            return self._csv_to_excel(f, dst)
        if "Excel \u2192 CSV" in conv_type and ext in (".xlsx", ".xls"):
            return self._excel_to_csv(f, dst)

        return ConversionResult(ok=False, file=f, error="unsupported conversion type")

    # ------------------------------------------------------------------
    # Individual converters (lazy imports so missing libs don't break import)
    # ------------------------------------------------------------------

    def _excel_to_pdf(self, f: str, dst: str) -> ConversionResult:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            return ConversionResult(ok=False, file=f, error="install: pip install reportlab openpyxl")
        try:
            from openpyxl import load_workbook
        except ImportError:
            return ConversionResult(ok=False, file=f, error="install: pip install reportlab openpyxl")

        wb = load_workbook(f)
        ws = wb.active
        cv = canvas.Canvas(dst + ".pdf", pagesize=A4)
        y = 800
        for row in ws.iter_rows(values_only=True):
            cv.drawString(40, y, "  ".join(str(cell or "") for cell in row))
            y -= 20
        cv.save()
        return ConversionResult(ok=True, file=f, output=dst + ".pdf")

    def _pdf_to_word(self, f: str, dst: str) -> ConversionResult:
        try:
            from pdf2docx import Converter
        except ImportError:
            return ConversionResult(ok=False, file=f, error="install: pip install pdf2docx")
        cv = Converter(f)
        cv.convert(dst + ".docx")
        cv.close()
        return ConversionResult(ok=True, file=f, output=dst + ".docx")

    def _word_to_pdf(self, f: str, dst: str) -> ConversionResult:
        try:
            from docx2pdf import convert as w2p
        except ImportError:
            return ConversionResult(ok=False, file=f, error="install: pip install docx2pdf")
        w2p(f, dst + ".pdf")
        return ConversionResult(ok=True, file=f, output=dst + ".pdf")

    def _images_to_pdf(self, f: str, dst: str) -> ConversionResult:
        try:
            from PIL import Image
        except ImportError:
            return ConversionResult(ok=False, file=f, error="install: pip install Pillow")
        img = Image.open(f).convert("RGB")
        img.save(dst + ".pdf")
        return ConversionResult(ok=True, file=f, output=dst + ".pdf")

    def _pdf_to_txt(self, f: str, dst: str) -> ConversionResult:
        try:
            import pdfplumber
        except ImportError:
            return ConversionResult(ok=False, file=f, error="install: pip install pdfplumber")
        with pdfplumber.open(f) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        with open(dst + ".txt", "w", encoding="utf-8") as tf:
            tf.write(text)
        return ConversionResult(ok=True, file=f, output=dst + ".txt")

    def _csv_to_excel(self, f: str, dst: str) -> ConversionResult:
        try:
            from openpyxl import Workbook
        except ImportError:
            return ConversionResult(ok=False, file=f, error="install: pip install openpyxl")
        wb = Workbook()
        ws = wb.active
        with open(f, encoding="utf-8") as cf:
            for row in csv.reader(cf):
                ws.append(row)
        wb.save(dst + ".xlsx")
        return ConversionResult(ok=True, file=f, output=dst + ".xlsx")

    def _excel_to_csv(self, f: str, dst: str) -> ConversionResult:
        try:
            from openpyxl import load_workbook
        except ImportError:
            return ConversionResult(ok=False, file=f, error="install: pip install openpyxl")
        wb = load_workbook(f)
        ws = wb.active
        with open(dst + ".csv", "w", newline="", encoding="utf-8") as cf:
            w = csv.writer(cf)
            for row in ws.iter_rows(values_only=True):
                w.writerow(row)
        return ConversionResult(ok=True, file=f, output=dst + ".csv")
