$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location $PSScriptRoot

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment Python not found: $Python"
}

Write-Host "=== AFIP Milestone S Cleanup Pack 3 — Source Evidence ==="
& $Python -m tools.afip_cleanup_execution_stop

Write-Host "Running focused tests..."
& $Python -m pytest tests\test_milestone_s_cleanup_pack_3.py -v

Write-Host "Collecting exact allocation/protection/execution source..."
& $Python -m tools.afip_cleanup_pack_3_source_evidence

Write-Host ""
Write-Host "Send this result file back:"
Write-Host "runtime\architecture_cleanup_pack_3\AFIP_CLEANUP_PACK_3_SOURCE_EVIDENCE_RESULT.zip"
Write-Host ""
Write-Host "No runtime logic has been changed."
