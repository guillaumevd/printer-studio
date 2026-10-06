"""Packaged-app smoke test. Always simulated, with isolated temporary logs."""
import json
from pathlib import Path
import tempfile
import threading
import time


def run(report):
    import webview
    from app.firmware.catalog import catalog
    from app.desktop.window import show_window
    from app.printer.transports import DemoDevice, NativeDevice
    from app.web.server import make_server
    from app.printer.service import PrinterService
    from app.core.paths import VERSION
    result = {"version": VERSION, "usb_access": False}
    import sys
    if getattr(sys, "frozen", False):
        from app.validation.bundle import verify_bundle
        result["bundle"] = verify_bundle(Path(sys.executable).parent)
    report = Path(report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    def checkpoint(stage):
        result["stage"] = stage
        report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    checkpoint("starting")
    with tempfile.TemporaryDirectory() as folder:
        device = DemoDevice()
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
                for _ in range(500):
                    for candidate in list(webview.windows):
                        if not candidate.events.loaded.is_set():
                            continue
                        location = candidate.get_current_url()
                        if not location:
                            continue
                        if location.endswith('/splash.html'):
                            from System.Windows.Forms import Screen
                            if candidate.native.Visible and "first_visible_splash" not in result:
                                bounds = candidate.native.Bounds
                                area = Screen.FromControl(candidate.native).WorkingArea
                                result["first_visible_splash"] = dict(
                                    started_hidden=candidate.hidden,
                                    centered=abs(bounds.X + bounds.Width / 2 - area.X - area.Width / 2) <= 1
                                        and abs(bounds.Y + bounds.Height / 2 - area.Y - area.Height / 2) <= 1,
                                    x=bounds.X, y=bounds.Y)
                            layout = candidate.evaluate_js("({fits:document.documentElement.scrollHeight <= innerHeight, width:innerWidth,height:innerHeight})")
                            if layout:
                                result["splash"] = dict(width=candidate.native.Width, height=candidate.native.Height,
                                    border=str(candidate.native.FormBorderStyle), layout=layout)
                        elif candidate.evaluate_js("document.body.dataset.ready === 'true'"):
                            window = candidate
                            break
                    if window:
                        break
                    time.sleep(.1)
                assert window, "Workspace did not load"
                checkpoint("workspace_loaded")
                for _ in range(100):
                    if str(window.native.WindowState) == "Maximized":
                        break
                    time.sleep(.05)
                assert abs(result["splash"]["layout"]["width"] - 400) <= 1 and abs(result["splash"]["layout"]["height"] - 500) <= 1, result
                assert result["splash"]["border"] == "None", result
                assert result["splash"]["layout"]["fits"], result
                assert result["first_visible_splash"]["started_hidden"] and result["first_visible_splash"]["centered"], result
                result["fullscreen"] = bool(window.native.is_fullscreen)
                result["maximized"] = str(window.native.WindowState) == "Maximized"
                result["window_border"] = str(window.native.FormBorderStyle)
                assert result["maximized"] and not result["fullscreen"], result
                assert result["window_border"] != "None", result
                result["ui"] = window.evaluate_js("({language:document.documentElement.lang,restorePresent:!!document.getElementById('di-restore'),firmwareCards:document.querySelectorAll('.firmware-tile').length,model:document.getElementById('model').textContent,mediaIconsLoaded:Array.from(document.querySelectorAll('.firmware-visual img')).every(i=>i.complete && i.naturalWidth>0)})")
                assert result["ui"]["language"] == "en"
                assert not result["ui"]["restorePresent"]
                assert result["ui"]["firmwareCards"] == 6 and result["ui"]["mediaIconsLoaded"]
                result["tabs"] = window.evaluate_js("({logsHidden:document.getElementById('activity').hidden,firmwareHidden:document.getElementById('firmwares').hidden,fits:document.documentElement.scrollHeight<=innerHeight})")
                assert all(result["tabs"].values()), result["tabs"]
                window.evaluate_js("document.querySelector('[href=\"#activity\"]').click()")
                assert window.evaluate_js("!document.getElementById('activity').hidden && document.getElementById('overview').hidden")
                window.evaluate_js("document.querySelector('[href=\"#firmwares\"]').click()")
                assert window.evaluate_js("!document.getElementById('firmwares').hidden && document.getElementById('activity').hidden")
                window.evaluate_js("document.querySelector('[data-version=\"DI-RS1 01.02\"]').click()")
                assert window.evaluate_js("document.getElementById('update').disabled"), "Already-original DI must not restore"
                window.evaluate_js("document.querySelector('[data-version=\"02.21\"]').click()")
                assert result["ui"]["model"] == "DI-RS1"
                result["di_ui"] = window.evaluate_js("({firmware:document.getElementById('firmware').textContent,serial:document.getElementById('detail-serial').textContent,cwd:document.getElementById('cwd').textContent,route:document.getElementById('route').textContent,enabled:!document.getElementById('update').disabled})")
                assert result["di_ui"]["firmware"].startswith("01.02")
                assert result["di_ui"]["serial"] == "DEMO-14002139"
                assert result["di_ui"]["cwd"] == "DI-RS1_300_0201.CWD"
                assert result["di_ui"]["enabled"]
                assert window.native.Icon is not None
                window.evaluate_js("document.querySelector('[data-version=\"02.21\"]').click(); document.getElementById('update').click(); document.getElementById('ack').click(); document.getElementById('confirm-start').click()")
                for _ in range(150):
                    if (service.snapshot().get("job") or {}).get("status") == "success":
                        break
                    time.sleep(.1)
                assert service.snapshot()["job"]["status"] == "success"
                assert service.snapshot()["job"]["steps"] == ["02.04", "02.07", "02.10", "02.21"]
                result["conversion_steps"] = service.snapshot()["job"]["steps"]
                checkpoint("stock_conversion_passed")
                for _ in range(60):
                    if window.evaluate_js("document.getElementById('model').textContent === 'DNP DS-RX1' && !document.querySelector('[data-version=\"02.10\"]').disabled"):
                        break
                    time.sleep(.1)
                window.evaluate_js("document.querySelector('[data-version=\"VG-02.21\"]').click(); document.getElementById('update').click(); document.getElementById('ack').click(); document.getElementById('confirm-start').click()")
                for _ in range(150):
                    if device.edition == "VG-02.21" and (service.snapshot().get("job") or {}).get("status") == "success":
                        break
                    time.sleep(.1)
                assert device.edition == "VG-02.21"
                for _ in range(100):
                    if window.evaluate_js("document.getElementById('model').textContent === 'DNP VG-RX1HS' && !document.querySelector('[data-version=\"02.21\"]').disabled"):
                        break
                    time.sleep(.1)
                assert window.evaluate_js("document.getElementById('model').textContent === 'DNP VG-RX1HS'")
                result["vg_ui"] = "passed"
                checkpoint("vg_install_passed")
                window.evaluate_js("document.querySelector('[data-version=\"02.21\"]').click(); document.getElementById('update').click(); document.getElementById('ack').click(); document.getElementById('confirm-start').click()")
                for _ in range(150):
                    if device.edition == "stock" and (service.snapshot().get("job") or {}).get("status") == "success":
                        break
                    time.sleep(.1)
                assert device.edition == "stock"
                result["vg_to_stock"] = "passed"
                checkpoint("vg_to_stock_passed")
                for _ in range(100):
                    if window.evaluate_js("!document.querySelector('[data-version=\"02.10\"]').disabled"):
                        break
                    time.sleep(.1)
                window.evaluate_js("document.querySelector('[data-version=\"02.10\"]').click(); document.getElementById('update').click(); document.getElementById('ack').click(); document.getElementById('confirm-start').click()")
                for _ in range(150):
                    if (service.snapshot().get("job") or {}).get("status") == "success" and device.firmware == "DS-RX1 02.10":
                        break
                    time.sleep(.1)
                assert device.firmware == "DS-RX1 02.10"
                for _ in range(100):
                    if window.evaluate_js("!document.querySelector('[data-version=\"DI-RS1 01.02\"]').disabled"):
                        break
                    time.sleep(.1)
                window.evaluate_js("document.querySelector('[data-version=\"DI-RS1 01.02\"]').click(); document.getElementById('update').click(); document.getElementById('ack').click(); document.getElementById('confirm-start').click()")
                for _ in range(150):
                    if (service.snapshot().get("job") or {}).get("status") == "success" and device.firmware == "DI-RS1 01.02":
                        break
                    time.sleep(.1)
                assert device.firmware == "DI-RS1 01.02"
                result["simulated_di_restore"] = "success"
                result["status"] = "passed"
                result["simulated_firmware"] = device.firmware
            except Exception as exc:
                result.update(status="failed", error=repr(exc))
            finally:
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text(json.dumps(result, indent=2), encoding="utf-8")
                for opened in list(webview.windows):
                    opened.destroy()

        threading.Thread(target=check, daemon=True).start()
        try:
            show_window(f"http://127.0.0.1:{server.server_port}", service.request_close, startup=True)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    if result.get("status") != "passed":
        raise RuntimeError("Self-test failed: " + str(result))
