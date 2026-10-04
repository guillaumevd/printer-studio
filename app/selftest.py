"""Packaged-app smoke test. Always simulated, with isolated temporary logs."""
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time


def run(report):
    import webview
    from .catalog import catalog, ROOT
    from .desktop import show_window
    from .devices import DemoDevice, NativeDevice
    from .server import make_server
    from .service import PrinterService
    from .paths import VERSION
    result = {"version": VERSION, "usb_access": False}
    report = Path(report).resolve()
    with tempfile.TemporaryDirectory() as folder:
        device = DemoDevice()
        device.firmware = "DS-RX1 02.21"
        service = PrinterService(device, Path(folder))
        service.scan()
        server = make_server(service, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def check():
            window = None
            try:
                assert all(item["available"] for item in catalog()), "Payload verification failed"
                NativeDevice()._command("probe")  # Validate bundled files; do not execute.
                for _ in range(300):
                    if webview.windows and webview.windows[0].events.loaded.is_set():
                        window = webview.windows[0]
                        break
                    time.sleep(.1)
                assert window, "Window did not load"
                for _ in range(100):
                    if window.evaluate_js("document.querySelectorAll('[data-version]').length") == 4:
                        break
                    time.sleep(.1)
                result["ui"] = window.evaluate_js("({language:document.documentElement.lang,restoreRemoved:!document.getElementById('restore'),model:document.getElementById('model').textContent})")
                assert result["ui"]["language"] == "en"
                assert result["ui"]["restoreRemoved"]
                assert result["ui"]["model"] == "DNP DS-RX1"
                assert window.native.Icon is not None
                window.evaluate_js("document.querySelector('[data-version=\"02.10\"]').click(); document.getElementById('update').click(); document.getElementById('ack').click(); document.getElementById('confirm-start').click()")
                for _ in range(150):
                    if (service.snapshot().get("job") or {}).get("status") == "success":
                        break
                    time.sleep(.1)
                assert service.snapshot()["job"]["status"] == "success"
                assert device.firmware == "DS-RX1 02.10"
                result["status"] = "passed"
                result["simulated_firmware"] = device.firmware
            except Exception as exc:
                result.update(status="failed", error=repr(exc))
            finally:
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text(json.dumps(result, indent=2), encoding="utf-8")
                if webview.windows:
                    webview.windows[0].destroy()

        threading.Thread(target=check, daemon=True).start()
        try:
            show_window(f"http://127.0.0.1:{server.server_port}", service.request_close)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    if result.get("status") != "passed":
        raise RuntimeError("Self-test failed: " + str(result))
