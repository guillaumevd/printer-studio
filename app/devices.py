"""Isolated Windows native transport and explicit simulation transport."""
import hashlib
import json
import os
import subprocess
import time
from .catalog import ROOT

class NativeDevice:
    demo = False

    def _command(self, *args):
        if os.name != "nt":
            raise RuntimeError("USB transport requires 64-bit Windows.")
        native = ROOT / "native"
        manifest = json.loads((native / "checksums.json").read_text())
        for name in ("PrinterBridge.exe", "cspstat64.dll"):
            if hashlib.sha256((native / name).read_bytes()).hexdigest() != manifest[name]:
                raise RuntimeError("Native component checksum mismatch: " + name)
        return [str(native / "PrinterBridge.exe"), *args]

    def probe(self):
        result = subprocess.run(self._command("probe"), capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=35,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(result.stdout.strip() or result.stderr.strip() or "Unable to read the USB device.")
        return json.loads(result.stdout)

    def flash(self, printer, target, path, emit):
        # Never terminate a writer on an HTTP timeout or browser disconnect.
        command = self._command("flash", printer["firmware"], printer["serial"], target, str(path))
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, encoding="utf-8", errors="replace",
                              creationflags=subprocess.CREATE_NO_WINDOW) as process:
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    event = {"message": line.strip()}
                emit(event.get("message", str(event)))
            if process.wait() != 0:
                raise RuntimeError("The step could not be verified. Review the log before trying again.")

class DemoDevice:
    demo = True

    def __init__(self):
        self.firmware = "DI-RS1 01.02"

    def probe(self):
        return [dict(model=91 if self.firmware.startswith("DI-") else 5,
                     firmware=self.firmware, serial="DEMO-14002139", status="0x00010001",
                     cwd="DI-RS1_300_0201.CWD", counter=37299, media=100, capacity=400)]

    def flash(self, printer, target, path, emit):
        for message in ("Simulation: checking printer identity", "Simulation: entering update mode",
                        "Simulation: transferring firmware", "Simulation: restarting and checking firmware version"):
            emit(message)
            time.sleep(0.6)
        self.firmware = "DS-RX1 " + target
