$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 2 ==="
Write-Host "Chronological Replay & Position Management Research Foundation"
python -m pytest -q tests/test_milestone_t_pack_2_chronological_replay.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Milestone T Pack 2 validation completed."
