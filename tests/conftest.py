import sys
from pathlib import Path

# Add automat/ to sys.path so tests can import core, i18n, app, etc.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "automat"))
