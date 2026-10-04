"""Console-free entry point for the desktop launcher."""
import ctypes
from app.main import main
from pathlib import Path

try:
    main()
except Exception as exc:
    ctypes.windll.user32.MessageBoxW(None, str(exc), "Printer Studio — startup error", 0x10)
