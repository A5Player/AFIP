$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pytest tests\test_afip_v1_dashboard_data_contract_phase_1.py -q
python -m pytest
python -m afip.dashboard_ui
Write-Host "AFIP V1 Dashboard Data Contract Phase 1: PASS" -ForegroundColor Green
