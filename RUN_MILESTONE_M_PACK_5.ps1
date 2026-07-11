$ErrorActionPreference = "Stop"

python -m pytest tests/test_milestone_m_pack_5.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m afip.dashboard_ui
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Milestone M Pack 5 validation completed successfully."
