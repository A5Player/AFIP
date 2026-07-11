$ErrorActionPreference = "Stop"
pytest tests/test_milestone_q_pack_10.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone Q Pack 10 validation completed. Review results before git commit/push."
