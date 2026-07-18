$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 3 ==="
Write-Host "Historical Replay Runner & Research Dataset Builder"
python -m pytest -q tests/test_milestone_t_pack_3_historical_replay_runner.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Milestone T Pack 3 validation completed."
