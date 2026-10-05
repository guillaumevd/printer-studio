"""Record every distributed file before building the installer and portable ZIP."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from app.core.paths import VERSION
from app.validation.bundle import file_hash, verify_bundle

folder = root / "dist/Printer Studio"
manifest = folder / "bundle-manifest.json"
files = {path.relative_to(folder).as_posix(): dict(size=path.stat().st_size, sha256=file_hash(path))
         for path in sorted(folder.rglob("*")) if path.is_file() and path != manifest}
manifest.write_text(json.dumps(dict(version=VERSION, files=files), indent=2), encoding="utf-8")
print(json.dumps(verify_bundle(folder)))
