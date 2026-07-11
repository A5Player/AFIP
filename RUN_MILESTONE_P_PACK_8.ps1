$ErrorActionPreference = "Stop"
pytest tests/test_milestone_p_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone P Pack 8 validation complete. Live execution remains disabled."
