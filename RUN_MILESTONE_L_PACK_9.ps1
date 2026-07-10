$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone L Pack 9 — Production Release Candidate ==="
python -m pytest tests/test_milestone_l_pack_9.py -v
python -m pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone L Pack 9 validation completed. Live execution remains disabled."
