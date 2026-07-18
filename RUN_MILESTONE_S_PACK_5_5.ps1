$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "AFIP virtual environment not found: $Python" }
Write-Host "=== AFIP Milestone S Pack 5.5 Validation ==="
& $Python -m pytest tests/test_milestone_s_pack_5_5.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Pack 5.5 targeted validation completed."
Write-Host "Next: .\.venv\Scripts\python.exe tools\afip_local_quality_check.py"
