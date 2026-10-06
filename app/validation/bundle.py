"""Offline integrity check of the complete standalone distribution."""
import hashlib
import json
from pathlib import Path

from app.core.paths import VERSION
from app.firmware.catalog import VERSIONS, HASHES
from app.firmware.di_support import FILENAME as DI_FILENAME, SHA256 as DI_SHA256
from app.firmware.vg_rx1hs import FILENAME as VG_FILENAME, SHA256 as VG_SHA256

VENDOR_DLL_HASH = "5973b9e0c6c1e2e359389a7a4036d249956878685dd04ec6667eef4ab22a65d4"


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_bundle(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder / "bundle-manifest.json").read_text(encoding="utf-8"))
    if manifest["version"] != VERSION:
        raise ValueError("Bundle version mismatch")
    entries = manifest["files"]
    required = {
        "Printer Studio.exe", "README.md", "Install WebView2.cmd",
        "runtime/MicrosoftEdgeWebview2Setup.exe",
        "_internal/python312.dll", "_internal/base_library.zip",
        "_internal/native/PrinterBridge.exe", "_internal/native/cspstat64.dll",
        "_internal/native/checksums.json", "_internal/web/index.html",
        "_internal/web/splash.html", "_internal/web/assets/printer.ico",
    } | {f"_internal/firmware/{version}.bin" for version in VERSIONS} | {f"_internal/firmware/{DI_FILENAME}", f"_internal/firmware/{VG_FILENAME}"}
    if not required.issubset(entries):
        raise ValueError("Missing required bundle entries: " + ", ".join(sorted(required - entries.keys())))
    for relative, expected in entries.items():
        path = (folder / relative).resolve()
        if not path.is_relative_to(folder) or not path.is_file():
            raise ValueError("Missing or invalid bundle path: " + relative)
        if path.stat().st_size != expected["size"] or file_hash(path) != expected["sha256"]:
            raise ValueError("Bundle integrity mismatch: " + relative)
    for version, digest in zip(VERSIONS, HASHES):
        if file_hash(folder / f"_internal/firmware/{version}.bin") != digest.lower():
            raise ValueError("Unrecognized firmware image: " + version)
    if file_hash(folder / "_internal/native/cspstat64.dll") != VENDOR_DLL_HASH:
        raise ValueError("Unrecognized vendor USB library")
    if file_hash(folder / f"_internal/firmware/{DI_FILENAME}") != DI_SHA256.lower():
        raise ValueError("Unrecognized original DI firmware image")
    if file_hash(folder / f"_internal/firmware/{VG_FILENAME}") != VG_SHA256.lower():
        raise ValueError("Unrecognized VG-RX1HS firmware image")
    return dict(status="passed", version=VERSION, files_verified=len(entries), usb_access=False)
