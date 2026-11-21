"""
Optional dependency registry — centralizes soft-dependency checks so
features degrade gracefully instead of scattering try/except ImportError
throughout the codebase.

Usage:

    from automat.core.optional_deps import deps

    if deps.has("openpyxl"):
        ...
    else:
        deps.require("openpyxl")   # -> raises DependencyMissing with install hint

Or as a decorator:

    @deps.requires("pdfplumber", "pdfplumber")
    def extract_pdf_text(path): ...
"""

from functools import wraps
from importlib import import_module
from typing import Callable


class DependencyMissing(Exception):
    """Raised when an optional dependency is required but not installed."""

    def __init__(self, module: str, package: str, feature: str = ""):
        self.module = module
        self.package = package
        self.feature = feature
        msg = f"Optional dependency '{package}' is required for {feature or module}. " \
              f"Install: pip install {package}"
        super().__init__(msg)


# module_name -> (pip_package, human_readable_feature)
_REGISTRY: dict[str, tuple[str, str]] = {
    "openpyxl": ("openpyxl", "Excel XLSX read/write"),
    "reportlab": ("reportlab", "PDF generation from Excel"),
    "pdf2docx": ("pdf2docx", "PDF to Word conversion"),
    "docx2pdf": ("docx2pdf", "Word to PDF conversion"),
    "PIL": ("Pillow", "Images to PDF conversion"),
    "pdfplumber": ("pdfplumber", "PDF text extraction"),
    "requests": ("requests", "HTTP API calls and data fetching"),
    "fitz": ("PyMuPDF", "PDF rendering and manipulation"),
    "yaml": ("PyYAML", "YAML parsing"),
    "paramiko": ("paramiko", "SSH client connections"),
    "git": ("GitPython", "Git repository operations"),
    "telethon": ("telethon", "Telegram client API"),
    "psycopg2": ("psycopg2-binary", "PostgreSQL database access"),
    "pyqtgraph": ("pyqtgraph", "Advanced charting"),
}


class OptionalDeps:
    """Registry and checker for optional third-party dependencies."""

    def __init__(self):
        self._cache: dict[str, bool] = {}

    def has(self, module: str) -> bool:
        """Return True if the module can be imported."""
        if module in self._cache:
            return self._cache[module]
        try:
            import_module(module)
            self._cache[module] = True
        except ImportError:
            self._cache[module] = False
        return self._cache[module]

    def missing(self) -> list[str]:
        """Return list of module names that are not installed."""
        return [m for m in _REGISTRY if not self.has(m)]

    def require(self, module: str, feature: str = "") -> None:
        """Raise DependencyMissing if the module is not installed."""
        if not self.has(module):
            package, _ = _REGISTRY.get(module, (module, module))
            raise DependencyMissing(module, package, feature or module)

    def check(self, module: str, feature: str = "") -> bool:
        """Return True if available, False otherwise (no exception)."""
        return self.has(module)

    def requires(self, module: str, feature: str = "") -> Callable:
        """Decorator: raise DependencyMissing if the module is missing."""

        def decorator(fn: Callable) -> Callable:
            @wraps(fn)
            def wrapper(*args, **kwargs):
                self.require(module, feature)
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    def install_hint(self, module: str) -> str:
        """Return a 'pip install X' hint for the given module."""
        package, feature = _REGISTRY.get(module, (module, module))
        return f"pip install {package}  # needed for {feature}"


# Singleton instance
deps = OptionalDeps()
