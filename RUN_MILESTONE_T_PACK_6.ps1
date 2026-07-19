$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone T Pack 6 ==="
Write-Host "Robustness, Walk-Forward Validation & Research Promotion Evidence Gate"

python -m pytest -q tests/test_milestone_t_pack_6_research_validation.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python tools/afip_local_quality_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Milestone T Pack 6 validation completed."
