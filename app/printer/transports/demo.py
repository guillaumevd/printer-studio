"""Explicit simulation transport; no USB calls."""
import time

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
