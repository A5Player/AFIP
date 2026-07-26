$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "AFIP V1 Runtime Truth & MT5 Preflight Certification"
python -m pytest `
  tests\test_afip_v1_dashboard_runtime_truth_preflight.py `
  tests\test_afip_v1_single_runtime_truth_refactor.py `
  -v

python -m afip.dashboard_ui

Write-Host "PASS: focused tests and dashboard generation completed"
Write-Host "Open: runtime\dashboard\afip_unified_dashboard.html"
Write-Host "Open: runtime\dashboard\afip_dashboard_audit.html"
