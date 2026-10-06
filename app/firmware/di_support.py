"""Original DI firmware recovered locally; never use a donor's full flash dump."""
import hashlib
from app.core.paths import ROOT

TARGET = "DI-RS1 01.02"
FILENAME = "DI-RS1_0102.bin"
SHA256 = "7E4A39F68791A670487B9116A92AD6A4E2D1AE938FCF4AF5A3E2E747331AAD8A"
SIZE = 1009156


def verify():
    path = ROOT / "firmware" / FILENAME
    if not path.is_file() or path.stat().st_size != SIZE or hashlib.sha256(path.read_bytes()).hexdigest().upper() != SHA256:
        raise ValueError("Original DI firmware is missing or its checksum does not match.")
    return path


def status():
    try:
        verify()
        error = None
    except ValueError as exc:
        error = str(exc)
    return dict(version=TARGET, sha256=SHA256, size=SIZE, available=error is None,
                error=error, hardware_tested=True, converted_di_only=True)
