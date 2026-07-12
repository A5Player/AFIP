$ErrorActionPreference = "Stop"
pytest tests/test_milestone_r_pack_4.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Milestone R Pack 4 validation PASS"
