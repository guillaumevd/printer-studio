"""Create the integrity manifest uploaded alongside a GitHub release installer."""
import hashlib
import json
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from app.paths import VERSION
installer = root / "release" / f"PrinterStudio-Setup-{VERSION}-x64.exe"
manifest = dict(version=VERSION, filename=installer.name, size=installer.stat().st_size,
                sha256=hashlib.sha256(installer.read_bytes()).hexdigest())
(root / "release/update-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest))
