$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$TemporaryRoot = Join-Path $ProjectRoot ".tmp"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Project-local virtual environment is missing. Run scripts\bootstrap.ps1 first."
}

New-Item -ItemType Directory -Force -Path $TemporaryRoot | Out-Null
$env:TEMP = $TemporaryRoot
$env:TMP = $TemporaryRoot
$env:PYTHONPYCACHEPREFIX = Join-Path $TemporaryRoot "python-cache"
$env:XDG_CACHE_HOME = Join-Path $TemporaryRoot "xdg-cache"

Push-Location $ProjectRoot
try {
    & $Python -m compileall -q supplyguard tests
    & $Python -m unittest discover -s tests -p "test_*.py" -v
}
finally {
    Pop-Location
}
