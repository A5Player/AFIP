$ErrorActionPreference = "Stop"
pytest tests/test_milestone_s_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
Write-Host "Milestone S Pack 1 validation complete."
Write-Host "Start runner: python afip.py run-locked-simulation"
