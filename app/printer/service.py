"""Serialized device access, update planning and persistent operation logs."""
from datetime import datetime, timezone
import copy
import json
import threading
import uuid
from app.firmware.catalog import plan, verify, firmware_name
from app.core.paths import DATA_ROOT

ALLOWED_STATUS = {"0x00010001", "0x00010008", "0x00010010", "0x00020008"}

class PrinterService:
    def __init__(self, device, logs=None):
        self.device = device
        self.lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.printers = []
        self.error = None
        self.job = None
        self.stopping = False
        self.logs = logs or DATA_ROOT / "logs" / ("demo" if device.demo else "device")
        self.logs.mkdir(parents=True, exist_ok=True)
        # A process interrupted during programming must never silently restart it.
        self.interrupted = (self.logs / "active.json").exists()

    def snapshot(self):
        with self.state_lock:
            return copy.deepcopy(dict(printers=self.printers, error=self.error, job=self.job,
                                      demo=self.device.demo, interrupted=self.interrupted))

    def scan(self):
        if not self.lock.acquire(blocking=False):
            return self.snapshot()
        try:
            printers = self.device.probe()
            with self.state_lock:
                self.printers, self.error = printers, None
        except Exception as exc:
            with self.state_lock:
                self.printers, self.error = [], str(exc)
        finally:
            self.lock.release()
        return self.snapshot()

    @staticmethod
    def validate(printers, serial, source):
        if len(printers) != 1:
            raise ValueError("Connect exactly one compatible printer to start an operation.")
        p = printers[0]
        if not serial or p.get("serial") != serial or p.get("firmware") != source:
            raise ValueError("The printer or its firmware has changed. Refresh detection.")
        if p.get("model") != (91 if source == "DI-RS1 01.02" else 5):
            raise ValueError("Incompatible model identity.")
        if p.get("status") not in ALLOWED_STATUS:
            raise ValueError("The current printer status does not allow a firmware change: " + p.get("status", "unknown"))
        return p

    def start(self, serial, source, target):
        if self.interrupted:
            raise ValueError("An operation was interrupted. Review logs/active.json and the README before continuing.")
        steps = plan(source, target)
        for version in steps:
            verify(version)
        if not self.lock.acquire(blocking=False):
            raise ValueError("A read or firmware change is already in progress.")
        try:
            if self.stopping:
                raise ValueError("The application is closing.")
            self.validate(self.device.probe(), serial, source)
            job = dict(id=uuid.uuid4().hex, status="running", steps=steps, completed=0,
                       source=source, target=target, serial=serial, events=[])
            (self.logs / "active.json").write_text(json.dumps(job), encoding="utf-8")
            with self.state_lock:
                self.job = job
            threading.Thread(target=self._run, args=(serial, source, steps), daemon=False).start()
        except Exception:
            self.lock.release()
            raise
        return self.snapshot()

    def request_close(self):
        """Prevent a close/start race; a writer or scan owns the same lock."""
        if not self.lock.acquire(blocking=False):
            return False
        try:
            self.stopping = True
            return True
        finally:
            self.lock.release()

    def emit(self, message):
        event = dict(time=datetime.now(timezone.utc).isoformat(), message=message)
        with self.state_lock:
            self.job["events"].append(event)
            job_id = self.job["id"]
        with (self.logs / (job_id + ".jsonl")).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _run(self, serial, source, steps):
        try:
            for target in steps:
                p = self.validate(self.device.probe(), serial, source)
                path = verify(target)
                destination = firmware_name(target)
                self.emit("Starting step: " + source + " → " + destination)
                self.device.flash(p, target, path, self.emit)
                printers = self.device.probe()
                self.validate(printers, serial, destination)
                if target == "VG-02.21" and printers[0].get("edition") != target:
                    raise ValueError("VG-RX1HS media edition was not confirmed after restart.")
                if target == "02.21" and printers[0].get("edition") != "stock":
                    raise ValueError("Stock DNP media edition was not confirmed after restart.")
                source = destination
                with self.state_lock:
                    self.printers = printers
                    self.job["completed"] += 1
                self.emit("Firmware version and serial number confirmed: " + source)
            with self.state_lock:
                self.job["status"] = "success"
            self.emit("Firmware change complete. You can now perform a test print.")
        except Exception as exc:
            with self.state_lock:
                self.job["status"] = "error"
                self.error = str(exc)
                self.interrupted = True
            self.emit(str(exc))
        finally:
            if not self.interrupted:
                (self.logs / "active.json").unlink(missing_ok=True)
            self.lock.release()
