$ErrorActionPreference = "Stop"
python -m pytest tests/test_milestone_p_pack_9.py -v
python -m pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone P Pack 9 validation completed. Live execution remains disabled."
