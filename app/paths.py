"""Read-only bundle assets and writable per-user application data."""
import os
import sys
from pathlib import Path

VERSION = "1.4.2"
DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Printer Studio" if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
