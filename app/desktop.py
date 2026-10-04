"""Native Windows window using Edge WebView2, with a matching taskbar icon."""
import ctypes
import os
import threading
from .catalog import ROOT

def show_window(url, can_close, startup=False, on_ready=None, update_test=None):
    import webview
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Guillaume.PrinterStudio")
    controller = None
    def open_app():
        window.resize(1320, 940)
        window.load_url(url)
        if on_ready:
            on_ready()
    if startup:
        from .startup import Startup
        controller = Startup(open_app, can_close, update_test)
    window = webview.create_window("Printer Studio · DI / DNP", url + "/splash.html" if startup else url,
                                   width=600 if startup else 1320, height=540 if startup else 940,
                                   min_size=(560, 500) if startup else (850, 650), background_color="#f5f6f3",
                                   text_select=True, js_api=controller)
    if controller:
        controller.window = window
        started = threading.Event()
        def loaded():
            if started.is_set():
                return
            started.set()
            threading.Thread(target=controller.check, daemon=True).start()
            if update_test:
                def exercise():
                    import time
                    for _ in range(200):
                        if controller.get_state()["status"] == "available":
                            # Exercise the actual splash button, not a separate install path.
                            time.sleep(.5)
                            window.evaluate_js("document.getElementById('install').click()")
                            return
                        time.sleep(.1)
                threading.Thread(target=exercise, daemon=True).start()
        window.events.loaded += loaded

    def set_icon():
        if os.name == "nt":
            from System.Drawing import Icon
            window.native.Icon = Icon(str(ROOT / "web" / "assets" / "printer.ico"))

    def closing():
        if not can_close():
            ctypes.windll.user32.MessageBoxW(None,
                "An operation is in progress. Wait for it to finish before closing Printer Studio.",
                "Printer Studio", 0x40)
            return False
        if controller:
            controller.cancel()
        return True

    window.events.before_show += set_icon
    window.events.closing += closing
    webview.start(gui="edgechromium", debug=False)
