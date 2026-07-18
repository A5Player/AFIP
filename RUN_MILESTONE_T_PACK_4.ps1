$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 4 ==="
Write-Host "Exit, Loss-Control & Position Outcome Research Engine"
python -m pytest -q tests/test_milestone_t_pack_4_exit_outcome_research.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Milestone T Pack 4 validation completed."
