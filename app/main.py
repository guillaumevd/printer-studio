"""Local server and dedicated desktop window (Python 3.10+)."""
import argparse
import os
import threading
import webbrowser
import json
from pathlib import Path
from urllib.request import urlopen
from app.printer.transports import DemoDevice, NativeDevice
from app.web.server import make_server
from app.printer.service import PrinterService
from app.core.paths import DATA_ROOT, VERSION

def main():
    parser = argparse.ArgumentParser(description="DI / DNP Printer Studio")
    parser.add_argument("--demo", action="store_true", help="Simulation without USB access")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--browser", action="store_true", help="Open in a browser instead of the desktop window")
    parser.add_argument("--self-test", metavar="REPORT", help="Run isolated desktop simulation and write a JSON report")
    parser.add_argument("--verify-bundle", metavar="REPORT", help="Verify standalone files without USB access")
    parser.add_argument("--update-test", metavar="REPORT", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.verify_bundle:
        import sys
        from app.validation.bundle import verify_bundle
        if not getattr(sys, "frozen", False):
            raise RuntimeError("Bundle verification requires the standalone executable")
        report = Path(args.verify_bundle).resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(verify_bundle(Path(sys.executable).parent), indent=2), encoding="utf-8")
        return
    if args.self_test:
        from app.validation.selftest import run
        return run(args.self_test)
    if args.update_test:
        args.demo, args.port = True, 8766
    # Retain the lock handle for the entire process, including pending writers.
    if os.name == "nt":
        import msvcrt
        (DATA_ROOT / "logs").mkdir(parents=True, exist_ok=True)
        shared_locks = Path(os.environ["LOCALAPPDATA"]) / "Printer Studio"
        shared_locks.mkdir(parents=True, exist_ok=True)
        instance_lock = (shared_locks / ("demo.lock" if args.demo else "device.lock")).open("a+b")
        instance_lock.seek(0)
        try:
            msvcrt.locking(instance_lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            url = f"http://127.0.0.1:{args.port}"
            def remote_can_close():
                try:
                    with urlopen(url + "/api/state", timeout=3) as response:
                        state = json.load(response)
                    return (state.get("job") or {}).get("status") != "running"
                except Exception:
                    return True  # Closing this viewer does not stop the existing server.
            with urlopen(url + "/api/state", timeout=3) as response:
                state = json.load(response)
                if state.get("application") != "printer-studio" or state.get("version") != VERSION:
                    raise RuntimeError("An older instance is running. Close it before restarting.")
            if args.browser:
                webbrowser.open(url)
            elif not args.no_browser:
                from app.desktop.window import show_window
                show_window(url, remote_can_close)
            raise SystemExit(0)
    import ctypes
    ctypes.windll.kernel32.CreateMutexW.restype = ctypes.c_void_p
    app_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\PrinterStudio.Running")
    service = PrinterService(DemoDevice() if args.demo else NativeDevice())
    server = make_server(service, args.port)
    def scan():
        threading.Thread(target=service.scan, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Printer Studio : {url}" + (" — DEMONSTRATION" if args.demo else ""), flush=True)
    try:
        if args.no_browser or args.browser:
            scan()
            if args.browser:
                webbrowser.open(url)
            server.serve_forever()
        else:
            from app.desktop.window import show_window
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            try:
                show_window(url, service.request_close, startup=True, on_ready=service.scan, update_test=args.update_test)
            finally:
                server.shutdown()
                server_thread.join()
    except KeyboardInterrupt:
        print("Stopping the server. Any active firmware write must finish before exit.")
    finally:
        server.server_close()
