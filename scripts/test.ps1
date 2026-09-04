$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    uv run --no-sync pytest --cov --cov-report=term-missing
}
finally {
    Pop-Location
}
