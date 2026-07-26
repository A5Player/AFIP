$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pytest tests\test_afip_v1_dashboard_data_contract_phase_1.py tests\test_afip_v1_execution_pipeline_dashboard_phase_2.py -q
python -m pytest
python -m afip.dashboard_ui
Write-Host "AFIP V1 Execution Pipeline Dashboard Phase 2: PASS"
Write-Host "Open runtime\dashboard\afip_dashboard.html and select Execution Pipeline."
