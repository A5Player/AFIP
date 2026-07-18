$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "AFIP virtual-environment Python not found: $Python" }
Write-Host "=== AFIP Milestone S Pack 5.7 Validation ==="
& $Python -m pytest tests\test_milestone_s_pack_5_7.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python tools\validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Pack 5.7 targeted validation completed."
Write-Host "Next: .\.venv\Scripts\python.exe tools\afip_local_quality_check.py"
