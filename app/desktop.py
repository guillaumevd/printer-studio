"""Frameless startup splash and a fully loaded fullscreen Windows workspace."""
import ctypes
import os
import threading
import time
from .catalog import ROOT


def show_window(url, can_close, startup=False, on_ready=None, update_test=None):
    import webview
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Guillaume.PrinterStudio")
    controller = None
    handoff = threading.Event()
    cancelled = threading.Event()

    def set_icon(target):
        if os.name == "nt":
            from System.Drawing import Icon
            target.native.Icon = Icon(str(ROOT / "web" / "assets" / "printer.ico"))

    def close_workspace():
        if not can_close():
            ctypes.windll.user32.MessageBoxW(None,
                "An operation is in progress. Wait for it to finish before closing Printer Studio.",
                "Printer Studio", 0x40)
            return False
        return True

    def open_app():
        # Detection completes while the splash remains visible.
        if on_ready:
            on_ready()
        if cancelled.is_set():
            return
        main = webview.create_window("Printer Studio · DI / DNP", url,
            width=1320, height=940, min_size=(850, 650), hidden=True,
            background_color="#f5f6f3", text_select=True)
        main.events.before_show += lambda: set_icon(main)
        main.events.closing += close_workspace
        shown = threading.Event()

        def loaded():
            if shown.is_set():
                return
            shown.set()
            def reveal():
                for _ in range(200):
                    if cancelled.is_set():
                        main.destroy()
                        return
                    if main.evaluate_js("document.body.dataset.ready === 'true'"):
                        set_icon(main)
                        main.toggle_fullscreen()
                        main.show()
                        handoff.set()
                        window.destroy()
                        return
                    time.sleep(.05)
                # Keep a recoverable window visible if the local UI fails to initialize.
                main.show()
                handoff.set()
                window.destroy()
            threading.Thread(target=reveal, daemon=True).start()
        main.events.loaded += loaded

    if startup:
        from .startup import Startup, SplashAPI
        controller = Startup(open_app, can_close, update_test)
    window = webview.create_window("Printer Studio · DI / DNP",
        url + "/splash.html" if startup else url,
        width=400 if startup else 1320, height=500 if startup else 940,
        min_size=(400, 500) if startup else (850, 650),
        frameless=startup, resizable=not startup, easy_drag=startup,
        background_color="#f5f6f3", text_select=True, js_api=SplashAPI(controller) if controller else None)
    window.events.before_show += lambda: set_icon(window)
    if startup and os.name == "nt":
        def size_splash():
            from System import Action
            scale = window.native.scale_factor
            window.resize(round(400 * scale), round(500 * scale))
            def apply_size():
                # WinForms initially reserves a title bar even for a frameless view.
                # Center the final 400 x 500 logical-pixel client area after DPI scaling.
                window.native.CenterToScreen()
            if window.native.InvokeRequired:
                window.native.Invoke(Action(apply_size))
            else:
                apply_size()

    def closing():
        if handoff.is_set():
            return True
        if not close_workspace():
            return False
        cancelled.set()
        if controller:
            controller.cancel()
        return True
    window.events.closing += closing

    if controller:
        controller.window = window
        started = threading.Event()
        def loaded():
            if started.is_set():
                return
            started.set()
            if os.name == "nt":
                size_splash()
            threading.Thread(target=controller.check, daemon=True).start()
            if update_test:
                def exercise():
                    for _ in range(200):
                        if controller.get_state()["status"] == "available":
                            time.sleep(.5)
                            window.evaluate_js("document.getElementById('install').click()")
                            return
                        time.sleep(.1)
                threading.Thread(target=exercise, daemon=True).start()
        window.events.loaded += loaded
    webview.start(gui="edgechromium", debug=False)
