param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [switch]$SkipFullRegression
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo

Write-Host "=== AFIP Phase U Pack 3.3.11 ===" -ForegroundColor Cyan
Write-Host "Runtime Research Data Git Isolation" -ForegroundColor Cyan

python -m pytest -q tests/test_phase_u_pack_3_3_11_runtime_research_git_isolation.py
if ($LASTEXITCODE -ne 0) {
    throw "Pack 3.3.11 targeted validation failed."
}

python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) {
    throw "Financial naming validation failed."
}

if (-not $SkipFullRegression) {
    Write-Host ""
    Write-Host "Running full regression..." -ForegroundColor Yellow
    python -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Full regression failed."
    }
}

Write-Host ""
Write-Host "PASS - Phase U Pack 3.3.11 validated." -ForegroundColor Green
Write-Host "Research data remains local and can be regenerated or resumed on VPS." -ForegroundColor Green
