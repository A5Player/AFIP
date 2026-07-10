$ErrorActionPreference = "Stop"
pytest tests/test_milestone_l_pack_10.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone L Pack 10 validation completed. Execution remains LOCKED_SIMULATION_ONLY."
