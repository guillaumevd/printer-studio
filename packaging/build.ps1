param([string]$InnoCompiler = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try {
    $python = Join-Path $projectRoot '.build-venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        py -3.12 -m venv .build-venv
        if ($LASTEXITCODE -ne 0) { throw 'Unable to create the build environment.' }
    }
    & $python -c "import sys, struct; assert sys.version_info[:2] == (3, 12) and struct.calcsize('P') == 8, 'Build with Python 3.12 x64.'"
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 x64 is required for this distribution.' }
    & $python -m pip install -r packaging/build-requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Build dependency installation failed.' }
    $version = & $python -c "from app.core.paths import VERSION; print(VERSION)"
    & ./native/build.ps1
    & ./tests/native/run.ps1
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    & $python -m PyInstaller --noconfirm packaging/PrinterStudio.spec
    if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
    $runtimeSetup = Join-Path $PSScriptRoot 'vendor\MicrosoftEdgeWebview2Setup.exe'
    $signature = Get-AuthenticodeSignature -LiteralPath $runtimeSetup
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Microsoft Corporation*') {
        throw 'A valid Microsoft-signed WebView2 bootstrapper is required in packaging/vendor.'
    }
    $distribution = Join-Path $projectRoot 'dist/Printer Studio'
    Copy-Item README.md (Join-Path $distribution 'README.md')
    New-Item -ItemType Directory -Path (Join-Path $distribution 'docs') -Force | Out-Null
    Copy-Item 'docs\*' (Join-Path $distribution 'docs') -Recurse -Force
    New-Item -ItemType Directory -Path (Join-Path $distribution 'runtime') -Force | Out-Null
    Copy-Item $runtimeSetup (Join-Path $distribution 'runtime/MicrosoftEdgeWebview2Setup.exe')
    Copy-Item (Join-Path $PSScriptRoot 'Install WebView2.cmd') $distribution
    & $python packaging/bundle_manifest.py
    if ($LASTEXITCODE -ne 0) { throw 'Bundle verification failed.' }
    if (-not $InnoCompiler) { $InnoCompiler = Join-Path $projectRoot '.build-tools\InnoSetup\ISCC.exe' }
    & $InnoCompiler "/DAppVersion=$version" packaging/installer.iss
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }
    Compress-Archive -LiteralPath 'dist\Printer Studio' -DestinationPath "release\PrinterStudio-Portable-$version-x64.zip" -Force
    & $python packaging/release_manifest.py
    if ($LASTEXITCODE -ne 0) { throw 'Release manifest failed.' }
    Get-FileHash release/*.exe, release/*.zip -Algorithm SHA256 | ForEach-Object {
        "$($_.Hash)  $([IO.Path]::GetFileName($_.Path))"
    } | Set-Content release/SHA256SUMS.txt
} finally { Pop-Location }
