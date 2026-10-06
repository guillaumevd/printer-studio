"""Hash-locked DNP images and the recovered, main-only original DI image."""
import hashlib

from app.core.paths import ROOT
from app.firmware import di_support, vg_rx1hs
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
    if version == vg_rx1hs.TARGET:
        return vg_rx1hs.verify()
    if version == di_support.TARGET:
        return di_support.verify()
    path = payload(version)
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest().upper() != HASHES[VERSIONS.index(version)]:
        raise ValueError("Firmware missing or checksum mismatch: " + version)
    return path

def plan(firmware, target):
    if target == vg_rx1hs.TARGET:
        return ([target] if firmware == "DS-RX1 02.21" else plan(firmware, "02.21") + [target])
    if target == di_support.TARGET:
        if firmware.startswith("DS-RX1 ") and firmware[7:] in VERSIONS:
            return [target]
        raise ValueError("DI restoration requires a converted DI-RS1 running supported DNP firmware.")
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
        if target == "02.21":
            return [target]  # Reinstall stock 2.21, including removal of VG media support.
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
    result.append(dict(**di_support.status(), name="DI-RS1",
                       description="Original DI Support 1.02 firmware, for DI Support media. Restores a converted DI-RS1 after checking its original DI bootloader, firmware image and printer identity. The donor printer's identity and settings are excluded. Factory DNP printers are not supported."))
    result.append(vg_rx1hs.catalog_entry())
    return result

def firmware_name(target):
    if target == vg_rx1hs.TARGET:
        return "DS-RX1 02.21"
    return target if target == di_support.TARGET else "DS-RX1 " + target
