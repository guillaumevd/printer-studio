"""Explicit simulation transport; no USB calls."""
import time
from app.firmware.catalog import firmware_name

class DemoDevice:
    demo = True

    def __init__(self):
        self.firmware = "DI-RS1 01.02"
        self.edition = "stock"

    def probe(self):
        return [dict(model=91 if self.firmware.startswith("DI-") else 5,
                     firmware=self.firmware, edition=self.edition,
                     display_name="DNP VG-RX1HS" if self.edition == "VG-02.21" else "DI-RS1" if self.firmware.startswith("DI-") else "DNP DS-RX1",
                     serial="DEMO-14002139", status="0x00010001",
                     cwd="DI-RS1_300_0201.CWD", counter=37299, media=100, capacity=400)]

    def flash(self, printer, target, path, emit):
        for message in ("Simulation: checking printer identity", "Simulation: entering update mode",
                        "Simulation: transferring firmware", "Simulation: restarting and checking firmware version"):
            emit(message)
            time.sleep(0.6)
        self.firmware = firmware_name(target)
        self.edition = "VG-02.21" if target == "VG-02.21" else "stock"
