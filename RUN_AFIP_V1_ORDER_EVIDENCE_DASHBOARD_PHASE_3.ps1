$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pytest tests/test_afip_v1_order_evidence_dashboard_phase_3.py tests/test_afip_v1_dashboard_data_contract_phase_1.py tests/test_afip_v1_execution_pipeline_dashboard_phase_2.py -q
python -m afip.dashboard_ui
Write-Host "AFIP V1 Order Evidence Dashboard Phase 3: PASS"
