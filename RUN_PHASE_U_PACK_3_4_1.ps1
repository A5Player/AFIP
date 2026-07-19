$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== AFIP Phase U Pack 3.4.1 ==="
Write-Host "Historical Dataset Readiness Certification"

python -m pytest tests/test_phase_u_pack_3_4_1.py -q
if ($LASTEXITCODE -ne 0) { throw "Pack tests failed." }

python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { throw "Financial naming validation failed." }

Write-Host ""
Write-Host "Running full regression..."
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Full regression failed." }

Write-Host ""
Write-Host "PASS - Phase U Pack 3.4.1 validated."
Write-Host "Historical datasets require certification before walk-forward research."
