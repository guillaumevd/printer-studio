"""Splash-screen state machine. Application updates happen before USB operations."""
import sys
import threading
import time
from . import updater
from .paths import DATA_ROOT, VERSION


class SplashAPI:
    """Expose only UI actions; never traverse native windows or internal locks."""
    def __init__(self, controller):
        self._controller = controller

    def get_state(self):
        return self._controller.get_state()

    def continue_app(self):
        return self._controller.continue_app()

    def install_update(self):
        return self._controller.install_update()


class Startup:
    def __init__(self, open_app, can_close, test_report=None):
        self.window = None
        self.open_app = open_app
        self.can_close = can_close
        self.test_report = test_report
        self.lock = threading.RLock()
        self.closed = False
        self.update = None
        self.state = dict(status="checking", message="Checking for application updates…",
                          current=VERSION, latest=None, progress=0)

    def get_state(self):
        with self.lock:
            return dict(self.state)

    def check(self):
        try:
            if not getattr(sys, "frozen", False):
                message = "Development mode · opening Printer Studio"
            else:
                update = updater.latest()
                with self.lock:
                    if self.closed:
                        return
                    if update:
                        self.update = update
                        self.state.update(status="available", latest=update["version"],
                                          message="A new version of Printer Studio is available.")
                        return
                message = "You're up to date · opening Printer Studio"
        except Exception:
            message = "Update check unavailable · continuing offline"
        with self.lock:
            if self.closed:
                return
            self.state.update(status="opening", message=message)
        time.sleep(1.2)
        self.continue_app()

    def continue_app(self):
        with self.lock:
            if self.closed or self.state["status"] in ("downloading", "installing"):
                return
            self.closed = True
            self.state.update(status="opening", message="Loading your printer workspace…")
        self.open_app()

    def install_update(self):
        with self.lock:
            if self.closed or self.state["status"] != "available" or not self.update:
                return
            self.state.update(status="downloading", message="Downloading application update…")
        threading.Thread(target=self._install, daemon=True).start()

    def _install(self):
        def progress(received, total):
            with self.lock:
                self.state["progress"] = round(received / total * 100)
        try:
            destination = updater.download(self.update, DATA_ROOT / "updates" / self.update["version"],
                                           progress, lambda: self.closed)
            with self.lock:
                if self.closed:
                    return
                updater.launch_installer(destination, self.update, self.test_report)
                self.state.update(status="installing", message="Installing update · Printer Studio will restart")
            self.window.destroy()
        except Exception as exc:
            with self.lock:
                if not self.closed:
                    self.state.update(status="error", message="Update not installed. " + str(exc))

    def cancel(self):
        with self.lock:
            self.closed = True
