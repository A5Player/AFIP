$ErrorActionPreference = "Stop"
pytest tests/test_milestone_o_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone O Pack 2 validation completed. Live execution remains disabled."
