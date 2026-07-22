param(
  [string]$ProjectRoot = "C:\AFIP\source"
)
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
Push-Location $ProjectRoot
try {
  & $Python -m pytest -q tests/test_afip_v1_final_maximum_lot_size_unit_policy.py
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host "Maximum Lot Size + Maximum Lot Unit policy tests PASS."
  Write-Host "Run full regression with: $Python -m pytest -q"
}
finally { Pop-Location }
