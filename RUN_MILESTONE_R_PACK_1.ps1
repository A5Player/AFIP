$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone R Pack 1 — Production Regression Audit ==="
python -m pytest tests/test_milestone_r_pack_1.py -v
python -m pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "=== Milestone R Pack 1 validation completed ==="
Write-Host "Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT"
