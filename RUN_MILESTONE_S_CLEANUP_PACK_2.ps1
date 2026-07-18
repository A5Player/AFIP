$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location $PSScriptRoot

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment Python not found: $Python"
}

Write-Host "=== AFIP Milestone S Cleanup Pack 2 ==="
& $Python -m tools.afip_cleanup_execution_stop

Write-Host "Running Pack 2 focused tests..."
& $Python -m pytest tests\test_milestone_s_cleanup_pack_2.py -v

Write-Host "Building responsibility and dependency matrix..."
& $Python -m tools.afip_architecture_responsibility_matrix

Write-Host ""
Write-Host "Reports:"
Write-Host "runtime\architecture_cleanup_pack_2\RESPONSIBILITY_MATRIX.md"
Write-Host "runtime\architecture_cleanup_pack_2\responsibility_matrix.json"
Write-Host "runtime\architecture_cleanup_pack_2\responsibility_matrix.csv"
Write-Host ""
Write-Host "Execution remains stopped. No runtime routing has been changed."
