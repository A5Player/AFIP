$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Virtual environment Python not found: $Python" }
Write-Host "=== AFIP Milestone S Pack 6.0 ==="
& $Python -m pytest tests\test_milestone_s_pack_6_0.py -v
if ($LASTEXITCODE -ne 0) { throw "Pack 6.0 tests failed." }
& $Python tools\afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { throw "Local quality check failed." }
Write-Host "Pack 6.0 validation complete. Execution authority remains NONE."
