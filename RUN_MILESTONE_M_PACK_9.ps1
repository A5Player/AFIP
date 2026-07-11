$ErrorActionPreference = "Stop"
pytest tests/test_milestone_m_pack_9.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone M Pack 9 validation complete."
