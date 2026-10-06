"""Read-only bundle assets and writable per-user application data."""
import os
import sys
from pathlib import Path

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
VERSION = "1.8.0"
DATA_ROOT = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Printer Studio" if getattr(sys, "frozen", False) else ROOT
