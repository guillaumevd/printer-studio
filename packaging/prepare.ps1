$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$assets = Get-Content (Join-Path $PSScriptRoot 'runtime-assets.json') -Raw | ConvertFrom-Json
$vendor = Join-Path $PSScriptRoot 'vendor'
New-Item -ItemType Directory -Path $vendor -Force | Out-Null
$archive = Join-Path $vendor 'runtime-assets.zip'
Invoke-WebRequest -Uri $assets.url -OutFile $archive
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $assets.sha256) { throw 'Runtime asset checksum mismatch' }
Expand-Archive -LiteralPath $archive -DestinationPath $projectRoot -Force
$webview = Join-Path $vendor 'MicrosoftEdgeWebview2Setup.exe'
Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $webview
$signature = Get-AuthenticodeSignature -LiteralPath $webview
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Microsoft Corporation*') { throw 'Invalid WebView2 bootstrapper signature' }
