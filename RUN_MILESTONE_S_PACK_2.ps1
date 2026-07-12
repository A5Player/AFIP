$ErrorActionPreference = "Stop"
if (Test-Path ".venv\Scripts\Activate.ps1") { . ".venv\Scripts\Activate.ps1" }
python tools/afip_four_profile_control.py status
pytest tests/test_milestone_s_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
python afip.py mt5-check
Write-Host "Milestone S Pack 2 validation completed. Execution remains LOCKED_SIMULATION_ONLY / NO_ORDER_SENT."
