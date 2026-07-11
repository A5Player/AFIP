$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone Q Pack 3 Validation ==="
python -m pytest tests/test_milestone_q_pack_3.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Milestone Q Pack 3 validation completed successfully."
