$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$TemporaryRoot = Join-Path $ProjectRoot ".tmp"
$VirtualEnvironment = Join-Path $ProjectRoot ".venv"

New-Item -ItemType Directory -Force -Path $TemporaryRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $TemporaryRoot "python-cache") | Out-Null

$env:TEMP = $TemporaryRoot
$env:TMP = $TemporaryRoot
$env:PYTHONPYCACHEPREFIX = Join-Path $TemporaryRoot "python-cache"
$env:XDG_CACHE_HOME = Join-Path $TemporaryRoot "xdg-cache"

if (-not (Test-Path -LiteralPath $VirtualEnvironment)) {
    python -m venv $VirtualEnvironment
}

$Python = Join-Path $VirtualEnvironment "Scripts\python.exe"
Push-Location $ProjectRoot
try {
    & $Python -m supplyguard --version
}
finally {
    Pop-Location
}
Write-Output "SupplyGuard isolated environment is ready at $VirtualEnvironment"
