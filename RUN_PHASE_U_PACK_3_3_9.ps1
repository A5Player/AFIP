param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

Write-Host "=== AFIP Phase U Pack 3.3.9 ===" -ForegroundColor Cyan
Write-Host "Historical readiness compatibility hotfix" -ForegroundColor Cyan

python -m pytest -q `
    tests/test_phase_u_pack_3_3_9_historical_readiness_compatibility.py `
    tests/test_production_milestone_h_pack_5.py `
    tests/test_production_milestone_h_pack_9.py

if ($LASTEXITCODE -ne 0) {
    throw "Targeted validation failed."
}

Write-Host ""
Write-Host "Running full regression..." -ForegroundColor Yellow
python -m pytest -q

if ($LASTEXITCODE -ne 0) {
    throw "Full regression failed."
}

Write-Host ""
Write-Host "PASS - Phase U Pack 3.3.9 validated." -ForegroundColor Green
