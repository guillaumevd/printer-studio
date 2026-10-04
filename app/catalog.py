"""Only the four payloads documented in the August 2026 conversion are accepted."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ["02.04", "02.07", "02.10", "02.21"]
HASHES = [
    "95115C6E13E2121E2640CE6DF214926BB3FC94EEF2549D6B4890062B6420772A",
    "BEB2799F45D90F7AED1070160CF4399542E3DF24FDECB6A000E3A84E91D029FC",
    "464ED3EB44FAE83633C00DD28455DCDF04A67AA7D99393F351D7BDAD726755A7",
    "840F80A230DB68C670DC7682FB83554D57A3ADD8BE8E2216D3DA26600EDEBB86",
]

def payload(version):
    if version not in VERSIONS:
        raise ValueError("Unknown version.")
    return ROOT / "firmware" / (version + ".bin")

def verify(version):
    path = payload(version)
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest().upper() != HASHES[VERSIONS.index(version)]:
        raise ValueError("Firmware missing or checksum mismatch: " + version)
    return path

def plan(firmware, target):
    if target not in VERSIONS:
        raise ValueError("Unknown target version.")
    if firmware == "DI-RS1 01.02":
        start = -1
    elif firmware.startswith("DS-RX1 ") and firmware[7:] in VERSIONS:
        start = VERSIONS.index(firmware[7:])
    else:
        raise ValueError("Unsupported source firmware. Normal application identification is required.")
    end = VERSIONS.index(target)
    if end == start:
        raise ValueError("This version is already installed.")
    if end < start:
        return [target]
    return VERSIONS[start + 1:end + 1]

def catalog():
    result = []
    for version, digest in zip(VERSIONS, HASHES):
        try:
            path = verify(version)
            error, size = None, path.stat().st_size
        except ValueError as exc:
            error, size = str(exc), 0
        result.append(dict(version=version, sha256=digest, available=error is None, size=size, error=error))
    return result
