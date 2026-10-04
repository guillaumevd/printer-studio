$ErrorActionPreference = 'Stop'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$sourceFile = Join-Path $PSScriptRoot 'PrinterBridge.cs'
$outputFile = Join-Path $PSScriptRoot 'PrinterBridge.exe'
& $compiler /nologo /platform:x64 /reference:System.Web.Extensions.dll "/out:$outputFile" $sourceFile
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
$manifest = @{}
foreach ($name in @('PrinterBridge.exe', 'cspstat64.dll')) {
    $manifest[$name] = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $PSScriptRoot $name)).Hash.ToLowerInvariant()
}
$json = $manifest | ConvertTo-Json
[System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'checksums.json'), $json, (New-Object System.Text.UTF8Encoding($false)))
