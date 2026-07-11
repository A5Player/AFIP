$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone Q Pack 7 — Market Intent Confidence Calibration ==="
python -m pytest tests/test_milestone_q_pack_7.py -v
python -m pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone Q Pack 7 validation completed successfully."
Write-Host "Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT."
