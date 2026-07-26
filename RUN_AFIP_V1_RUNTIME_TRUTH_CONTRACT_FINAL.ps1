$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "AFIP V1 Runtime Truth Contract Final Certification"
python -m pytest `
  tests\test_afip_v1_runtime_truth_contract_final.py `
  tests\test_afip_v1_runtime_truth_recovery_final.py `
  tests\test_afip_v1_dashboard_runtime_truth_preflight.py `
  tests\test_afip_v1_single_runtime_truth_refactor.py `
  -v

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "PASS: runtime truth compatibility and dashboard generation completed"
