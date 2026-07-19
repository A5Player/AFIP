$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "=== AFIP Phase U Pack 3.4.4 ==="
Write-Host "Research Evidence Consumer"

python -m pytest tests/test_phase_u_pack_3_4_4.py -q
if ($LASTEXITCODE -ne 0) { throw "Targeted tests failed." }

python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { throw "Financial naming validation failed." }

Write-Host ""
Write-Host "Running full regression..."
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Full regression failed." }

Write-Host ""
Write-Host "PASS - Phase U Pack 3.4.4 validated."
