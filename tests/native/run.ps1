$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$testExe = Join-Path $projectRoot 'build\NativeBridgeTests.exe'
$sources = @(Get-ChildItem -Path (Join-Path $projectRoot 'native') -Filter '*.cs' -Recurse |
    Where-Object Name -ne 'NativeApi.cs' | ForEach-Object FullName)
$sources += Join-Path $PSScriptRoot 'FakeNativeApi.cs'
New-Item -ItemType Directory -Path (Split-Path $testExe -Parent) -Force | Out-Null
& $compiler /nologo /platform:x64 /reference:System.Web.Extensions.dll /main:NativeBridgeTests "/out:$testExe" $sources
if ($LASTEXITCODE -ne 0) { throw 'Native test compilation failed.' }
& $testExe (Join-Path $projectRoot 'firmware')
if ($LASTEXITCODE -ne 0) { throw 'Native tests failed.' }
