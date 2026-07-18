$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Virtual environment Python not found: $Python" }
Write-Host "=== AFIP Milestone S Pack 5.9 ==="
& $Python -m pytest tests\test_milestone_s_pack_5_9.py -v
if ($LASTEXITCODE -ne 0) { throw "Pack 5.9 tests failed." }
& $Python tools\afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { throw "AFIP local quality check failed." }
Write-Host "Pack 5.9 validation complete. Execution authority remains NONE."
