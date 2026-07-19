$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location "C:\AFIP"

$packs = @("3_4_2", "3_4_3", "3_4_4", "3_4_5", "3_4_6", "3_4_7")
foreach ($pack in $packs) {
    & ".\APPLY_PHASE_U_PACK_${pack}_DOC_UPDATES.ps1"
}

python -m pytest `
  tests/test_phase_u_pack_3_4_2.py `
  tests/test_phase_u_pack_3_4_3.py `
  tests/test_phase_u_pack_3_4_4.py `
  tests/test_phase_u_pack_3_4_5.py `
  tests/test_phase_u_pack_3_4_6.py `
  tests/test_phase_u_pack_3_4_7.py -q
if ($LASTEXITCODE -ne 0) { throw "Combined targeted tests failed." }

python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { throw "Financial naming validation failed." }

Write-Host ""
Write-Host "Running full regression..."
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Full regression failed." }

Write-Host ""
Write-Host "PASS - Phase U Packs 3.4.2 through 3.4.7 validated."
