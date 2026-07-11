$ErrorActionPreference = "Stop"
python -m pytest tests/test_milestone_n_pack_5.py -v
python -m pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone N Pack 5 validation completed."
