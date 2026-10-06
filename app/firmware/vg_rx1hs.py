"""The locally validated three-media edition; stock DNP images stay separate."""
import hashlib
from app.core.paths import ROOT

TARGET = "VG-02.21"
NAME = "DNP VG-RX1HS"
FILENAME = "VG-RX1HS-02.21.bin"
SHA256 = "207264AEC62D21A373B51A16E45BA4C52214BC370B044C1DD1CEC92A98256A93"
SIZE = 1610056

def verify():
    path = ROOT / "firmware" / FILENAME
    if not path.is_file() or path.stat().st_size != SIZE or hashlib.sha256(path.read_bytes()).hexdigest().upper() != SHA256:
        raise ValueError("VG-RX1HS firmware missing or checksum mismatch.")
    return path

def catalog_entry():
    try:
        path = verify()
        error, size = None, path.stat().st_size
    except ValueError as exc:
        error, size = str(exc), 0
    return dict(version=TARGET, name=NAME, sha256=SHA256, size=size,
                available=error is None, error=error,
                description="DNP 2.21 with DNP, DI Support and Citizen CY-02 media support. Printing with all three was confirmed on the converted DI-RS1. Keeps the DS-RX1 USB identity for existing drivers and Hot Folder; external software may continue to display RX1HS.")
