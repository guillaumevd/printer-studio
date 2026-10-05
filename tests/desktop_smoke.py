"""Manual integration test: launches WebView2 and exits after checking DOM and icon.

Run from the project root: python -m tests.desktop_smoke
"""
import json
import tempfile
import threading
from pathlib import Path
import webview
from app.desktop.window import show_window
from app.printer.transports import DemoDevice
from app.printer.service import PrinterService
from app.web.server import make_server

with tempfile.TemporaryDirectory() as folder:
    service = PrinterService(DemoDevice(), Path(folder))
    service.device.firmware = "DS-RX1 02.21"
    service.scan()
    server = make_server(service, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    result = {}

    def verify():
        import time
        for _ in range(100):
            if webview.windows and webview.windows[0].events.loaded.is_set():
                break
            time.sleep(.1)
        window = webview.windows[0]
        time.sleep(2)
        try:
            result.update(window.evaluate_js("({title:document.title, model:document.getElementById('model').textContent, restoreRemoved:!document.getElementById('restore'), language:document.documentElement.lang, illustration:document.querySelector('.printer-visual img').getAttribute('src')})"))
            result["icon"] = window.native.Icon is not None
            result["icon_width"] = window.native.Icon.Width
            assert result["model"] == "DNP DS-RX1", result
            assert result["restoreRemoved"] and result["language"] == "en", result
            window.evaluate_js("document.querySelector('[data-version=\"02.04\"]').click()")
            result["downgrade"] = window.evaluate_js("({route:document.getElementById('route').textContent,title:document.getElementById('update-title').textContent,enabled:!document.getElementById('update').disabled})")
            assert result["downgrade"]["enabled"], result
            assert result["downgrade"]["route"] == "02.21→02.04", result
            window.evaluate_js("document.getElementById('update').click(); document.getElementById('ack').click(); document.getElementById('confirm-start').click()")
            for _ in range(100):
                if (service.snapshot().get("job") or {}).get("status") == "success":
                    break
                time.sleep(.1)
            assert service.snapshot()["job"]["status"] == "success", service.snapshot()
            assert service.device.firmware == "DS-RX1 02.04"
            result["simulated_downgrade"] = "success"
            assert result["icon"], result
            print(json.dumps(result, ensure_ascii=True), flush=True)
        except Exception as exc:
            result["error"] = str(exc)
        finally:
            window.destroy()

    threading.Thread(target=verify, daemon=True).start()
    try:
        show_window(f"http://127.0.0.1:{server.server_port}", service.request_close)
    finally:
        server.shutdown(); server.server_close(); thread.join()
    if "error" in result:
        raise RuntimeError(result["error"])
