$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone Q Pack 4 — Market Intent Statistics ==="
python -m pytest tests/test_milestone_q_pack_4.py -v
python -m pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone Q Pack 4 validation completed."
