$ErrorActionPreference = "Stop"
pytest tests/test_milestone_o_pack_10.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone O Pack 10 validation completed. Milestone O is complete. Live execution remains disabled."
