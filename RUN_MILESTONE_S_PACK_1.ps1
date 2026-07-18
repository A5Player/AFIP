$ErrorActionPreference = "Stop"

Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location $PSScriptRoot

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment Python not found: $Python"
}

Write-Host "=== AFIP Milestone S Cleanup Pack 3 ==="

& $Python -m tools.afip_cleanup_execution_stop

Write-Host ""
Write-Host "Running focused tests..."

& $Python -m pytest tests\test_milestone_s_cleanup_pack_3.py -v

if ($LASTEXITCODE -ne 0) {
    throw "Tests failed."
}

Write-Host ""
Write-Host "Collecting source evidence..."

& $Python -m tools.afip_cleanup_pack_3_source_evidence

if ($LASTEXITCODE -ne 0) {
    throw "Source evidence collection failed."
}

Write-Host ""
Write-Host "Completed."
Write-Host ""
Write-Host "Result:"
Write-Host "runtime\architecture_cleanup_pack_3\AFIP_CLEANUP_PACK_3_SOURCE_EVIDENCE_RESULT.zip"
Write-Host ""
Write-Host "No runtime logic has been changed."