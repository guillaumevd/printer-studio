"""Console-free entry point for the desktop launcher."""
import ctypes
import sys
from app.main import main

try:
    main()
except Exception as exc:
    if "--self-test" in sys.argv or "--verify-bundle" in sys.argv:
        sys.exit(1)
    ctypes.windll.user32.MessageBoxW(None, str(exc), "Printer Studio â€” startup error", 0x10)
