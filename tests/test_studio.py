import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from app.firmware.catalog import catalog, plan, verify, VERSIONS
from app.printer.transports import DemoDevice
from app.printer.service import PrinterService
from app.web.server import make_server

class FastDevice(DemoDevice):
    def flash(self, printer, target, path, emit):
        self.firmware = "DS-RX1 " + target
        emit("Simulated " + target)

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = PrinterService(FastDevice(), Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def wait_job(self):
        for _ in range(200):
            if self.service.lock.acquire(False):
                self.service.lock.release()
                return self.service.snapshot()["job"]
            time.sleep(.01)
        self.fail("Job did not terminate")

    def test_catalog_integrity(self):
        self.assertTrue(all(x["available"] for x in catalog()))
        with self.assertRaises(ValueError): verify("../../unknown")

    def test_plan(self):
        self.assertEqual(plan("DI-RS1 01.02", "02.21"), ["02.04", "02.07", "02.10", "02.21"])
        self.assertEqual(plan("DS-RX1 02.07", "02.21"), ["02.10", "02.21"])
        for source, target in [("DS-RX1 02.21", "02.21"), ("DI-RS1_RW_1.00", "02.04"), ("DS-RX1 01.10", "02.21")]:
            with self.assertRaises(ValueError): plan(source, target)

    def test_all_dnp_routes(self):
        for source_index, source in enumerate(VERSIONS):
            for target_index, target in enumerate(VERSIONS):
                with self.subTest(source=source, target=target):
                    if source_index == target_index:
                        with self.assertRaises(ValueError): plan("DS-RX1 " + source, target)
                    else:
                        expected = [target] if target_index < source_index else VERSIONS[source_index + 1:target_index + 1]
                        self.assertEqual(plan("DS-RX1 " + source, target), expected)
        with self.assertRaises(ValueError): plan("DS-RX1 02.21", "DI-RS1 01.02")

    def test_downgrade_verified(self):
        self.service.device.firmware = "DS-RX1 02.21"
        self.service.start("DEMO-14002139", "DS-RX1 02.21", "02.04")
        job = self.wait_job()
        self.assertEqual((job["status"], job["steps"], job["completed"]), ("success", ["02.04"], 1))
        self.assertEqual(self.service.snapshot()["printers"][0]["firmware"], "DS-RX1 02.04")
        self.assertFalse((self.service.logs / "active.json").exists())

    def test_downgrade_failed_verification(self):
        self.service.device.firmware = "DS-RX1 02.21"
        self.service.device.flash = lambda *args: None
        self.service.start("DEMO-14002139", "DS-RX1 02.21", "02.04")
        job = self.wait_job()
        self.assertEqual((job["status"], job["completed"]), ("error", 0))
        self.assertTrue(self.service.interrupted)

    def test_close_blocks_during_operation(self):
        self.service.lock.acquire()
        try:
            self.assertFalse(self.service.request_close())
            self.assertFalse(self.service.stopping)
        finally:
            self.service.lock.release()
        self.assertTrue(self.service.request_close())
        with self.assertRaisesRegex(ValueError, "closing"):
            self.service.start("DEMO-14002139", "DI-RS1 01.02", "02.04")

    def test_full_update_verified(self):
        self.service.start("DEMO-14002139", "DI-RS1 01.02", "02.21")
        job = self.wait_job()
        self.assertEqual((job["status"], job["completed"]), ("success", 4))
        self.assertFalse((self.service.logs / "active.json").exists())

    def test_identity_mismatch_no_write(self):
        with self.assertRaises(ValueError): self.service.start("wrong", "DI-RS1 01.02", "02.21")
        self.assertEqual(self.service.device.firmware, "DI-RS1 01.02")

    def test_multiple_printers_rejected(self):
        printer = self.service.device.probe()[0]
        with self.assertRaises(ValueError): self.service.validate([printer, printer], printer["serial"], printer["firmware"])

    def test_busy_printer_rejected(self):
        printer = self.service.device.probe()[0]
        printer["status"] = "0x00010002"
        with self.assertRaises(ValueError): self.service.validate([printer], printer["serial"], printer["firmware"])

    def test_failed_verification_stops_chain(self):
        self.service.device.flash = lambda *args: None
        self.service.start("DEMO-14002139", "DI-RS1 01.02", "02.21")
        job = self.wait_job()
        self.assertEqual((job["status"], job["completed"]), ("error", 0))
        self.assertTrue((self.service.logs / "active.json").exists())
        with self.assertRaises(ValueError): self.service.start("DEMO-14002139", "DI-RS1 01.02", "02.21")

    def test_mutual_exclusion(self):
        self.service.lock.acquire()
        try:
            with self.assertRaises(ValueError): self.service.start("DEMO-14002139", "DI-RS1 01.02", "02.21")
        finally:
            self.service.lock.release()

    def test_http_security_and_static(self):
        server = make_server(self.service, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        try:
            with urlopen(base + "/") as response:
                self.assertIn(b"My printer", response.read())
            with urlopen(base + "/api/state") as response:
                token = json.load(response)["token"]
            for path, headers, body, expected in [
                ("/api/update", {}, b"{}", 403),
                ("/api/update", {"X-Studio-Token": token}, b"{}", 409),
                ("/api/update", {"X-Studio-Token": token}, b"[]", 409),
                ("/api/scan", {"X-Studio-Token": token, "Origin": "https://evil.example"}, b"{}", 403),
                ("/api/state", {"Host": "evil.example"}, None, 403),
                ("/../run.py", {}, None, 404),
            ]:
                with self.assertRaises(HTTPError) as cm: urlopen(Request(base + path, data=body, headers=headers))
                self.assertEqual(cm.exception.code, expected)
            with urlopen(Request(base + "/api/scan", data=b"{}", headers={"X-Studio-Token": token})) as response:
                self.assertEqual(len(json.load(response)["printers"]), 1)
        finally:
            server.shutdown(); server.server_close(); thread.join()

if __name__ == "__main__":
    unittest.main()
