$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone T Pack 11 ==="
Write-Host "Complete Trade Plan, Capital Stewardship and Unattended Safety Foundation"

python -m pytest -q tests/test_milestone_t_pack_11_complete_trade_plan.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Milestone T Pack 11 validation completed."
