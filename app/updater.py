"""GitHub release discovery, bounded downloads and verified installer handoff."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from .paths import DATA_ROOT, VERSION

REPOSITORY = "guillaumevd/printer-studio"
API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
MAX_INSTALLER = 512 * 1024 * 1024


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"v?\d+\.\d+\.\d+", value):
        raise ValueError("Invalid release version")
    return tuple(map(int, value.lstrip("v").split(".")))


def read_json(url):
    request = Request(url, headers={"User-Agent": f"PrinterStudio/{VERSION}", "Accept": "application/json"})
    with urlopen(request, timeout=8) as response:
        body = response.read(1024 * 1024 + 1)
    if len(body) > 1024 * 1024:
        raise ValueError("Release metadata is too large")
    return json.loads(body)


def release_asset(release, name):
    tag = release["tag_name"]
    expected = f"https://github.com/{REPOSITORY}/releases/download/{tag}/{name}"
    assets = [a for a in release.get("assets", []) if a.get("name") == name]
    if len(assets) != 1 or assets[0].get("browser_download_url") != expected:
        raise ValueError("Missing or invalid release asset: " + name)
    return assets[0]


def validate_manifest(release, manifest):
    version = release["tag_name"].lstrip("v")
    version_tuple(version)
    name = f"PrinterStudio-Setup-{version}-x64.exe"
    if manifest.get("version") != version or manifest.get("filename") != name:
        raise ValueError("Release manifest does not match its tag")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", str(manifest.get("sha256", ""))):
        raise ValueError("Missing installer checksum")
    size = manifest.get("size")
    if type(size) is not int or not 0 < size <= MAX_INSTALLER:
        raise ValueError("Invalid installer size")
    asset = release_asset(release, name)
    if asset.get("size") != size:
        raise ValueError("Installer size differs from the manifest")
    return dict(version=version, filename=name, size=size, sha256=manifest["sha256"].lower(),
                url=asset["browser_download_url"])


def latest(current=VERSION):
    try:
        release = read_json(API_URL)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if release.get("draft") or release.get("prerelease"):
        return None
    if version_tuple(release.get("tag_name")) <= version_tuple(current):
        return None
    manifest_asset = release_asset(release, "update-manifest.json")
    return validate_manifest(release, read_json(manifest_asset["browser_download_url"]))


def download(update, folder, progress, cancelled=lambda: False):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / update["filename"]
    partial = destination.with_suffix(".part")
    received = 0
    digest = hashlib.sha256()
    started = time.monotonic()
    try:
        request = Request(update["url"], headers={"User-Agent": f"PrinterStudio/{VERSION}"})
        with urlopen(request, timeout=15) as response, partial.open("wb") as output:
            while True:
                if cancelled() or time.monotonic() - started > 300:
                    raise RuntimeError("Download cancelled or timed out")
                block = response.read(128 * 1024)
                if not block:
                    break
                received += len(block)
                if received > update["size"]:
                    raise ValueError("Downloaded installer exceeds the expected size")
                output.write(block)
                digest.update(block)
                progress(received, update["size"])
        if received != update["size"] or digest.hexdigest() != update["sha256"]:
            raise ValueError("Installer integrity check failed")
        partial.replace(destination)
        return destination
    finally:
        partial.unlink(missing_ok=True)


def ps_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def launch_installer(installer, update, test_report=None):
    """A detached helper waits for this process before replacing application files."""
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Install updates from the standalone application")
    executable = Path(sys.executable).resolve()
    installer = Path(installer).resolve()
    if hashlib.sha256(installer.read_bytes()).hexdigest() != update["sha256"]:
        raise ValueError("Installer checksum changed before installation")
    folder = installer.parent
    script = folder / "install-update.ps1"
    log = folder / "installer.log"
    result = folder / "handoff-result.json"
    # Values are PowerShell single-quoted literals; remote metadata never becomes code.
    restart_args = (" -ArgumentList @('--self-test', " + ps_literal('"' + str(Path(test_report).resolve()) + '"') + ")") if test_report else ""
    script.write_text(f"""$ErrorActionPreference = 'Stop'
$resultPath = {ps_literal(result)}
try {{
    $parent = Get-Process -Id {os.getpid()} -ErrorAction SilentlyContinue
    if ($parent) {{ Wait-Process -Id {os.getpid()} -Timeout 180 }}
    $installer = {ps_literal(installer)}
    if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant() -ne {ps_literal(update['sha256'])}) {{ throw 'Installer checksum mismatch' }}
    $setupArgs = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', {ps_literal('/DIR="' + str(executable.parent) + '"')}, {ps_literal('/LOG="' + str(log) + '"')})
    $setup = Start-Process -FilePath $installer -ArgumentList $setupArgs -WindowStyle Hidden -Wait -PassThru
    if ($setup.ExitCode -ne 0) {{ throw ('Installer returned ' + $setup.ExitCode) }}
    @{{status='installed';version={ps_literal(update['version'])}}} | ConvertTo-Json | Set-Content -LiteralPath $resultPath
    Start-Process -FilePath {ps_literal(executable)}{restart_args} -WorkingDirectory {ps_literal(executable.parent)} -WindowStyle Hidden
}} catch {{
    @{{status='failed';error=$_.Exception.Message}} | ConvertTo-Json | Set-Content -LiteralPath $resultPath
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show('Update installation failed. Your printer firmware was not changed. See ' + $resultPath, 'Printer Studio') | Out-Null
    exit 1
}}
""", encoding="utf-8-sig")
    powershell = Path(os.environ["WINDIR"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    subprocess.Popen([str(powershell), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                     creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
