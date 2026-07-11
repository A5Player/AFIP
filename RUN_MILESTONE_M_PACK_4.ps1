$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone M Pack 4 — Pattern Clustering ==="
python -m pytest tests/test_milestone_m_pack_4.py -v
python -m pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "=== Milestone M Pack 4 validation completed ==="
