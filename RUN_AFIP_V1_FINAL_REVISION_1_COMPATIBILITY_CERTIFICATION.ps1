$ErrorActionPreference = "Stop"

Write-Host "AFIP V1 Final Revision 1 - Compatibility Certification" -ForegroundColor Cyan

$RepoRoot = (Get-Location).Path
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host "`n=== $Name ===" -ForegroundColor Yellow
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
    Write-Host "PASS: $Name" -ForegroundColor Green
}

Invoke-Step "Targeted Compatibility Tests" {
    & $Python -m pytest -q `
        tests/test_phase_u_dashboard_live_mt5_fields.py `
        tests/test_phase_u_dashboard_internal_authority.py `
        tests/test_phase_u_final_dashboard_mt5_live.py `
        tests/test_phase_u_pack_3_4_11_unified_research.py `
        tests/test_afip_v1_final_revision_1_compatibility.py
}

Invoke-Step "Dashboard Build" {
    & $Python -m afip.dashboard_ui
}

Invoke-Step "AFIP Local Quality Check" {
    & $Python tools/afip_local_quality_check.py
}

Invoke-Step "Full Regression" {
    & $Python -m pytest -q
}

Write-Host "`n=== Git Status ===" -ForegroundColor Yellow
git status
Write-Host "`n=== Git Diff Names ===" -ForegroundColor Yellow
git diff --name-only
Write-Host "`n=== Git Cached Diff Names ===" -ForegroundColor Yellow
git diff --cached --name-only

Write-Host "`nAFIP V1 Final Revision 1 validation completed." -ForegroundColor Green
Write-Host "Do not use git add . Review and stage only the certified file list." -ForegroundColor Yellow
