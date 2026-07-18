$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location $PSScriptRoot

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment Python not found: $Python"
}

Write-Host "=== AFIP Milestone S Cleanup Pack 1 ==="
Write-Host "Stopping demo execution before architecture analysis..."
& $Python tools\afip_demo_execution_control.py stop-all

Write-Host "Running focused tests..."
& $Python -m pytest tests\test_milestone_s_cleanup_pack_1.py -v

Write-Host "Building complete architecture inventory..."
& $Python tools\afip_architecture_inventory.py

Write-Host ""
Write-Host "Reports:"
Write-Host "runtime\architecture_inventory\ARCHITECTURE_INVENTORY.md"
Write-Host "runtime\architecture_inventory\architecture_review.json"
Write-Host "runtime\architecture_inventory\components.csv"
Write-Host ""
Write-Host "Execution must remain stopped until the inventory is reviewed."
