$ErrorActionPreference = "Stop"
Write-Host "=== AFIP Milestone S Pack 7.3 - Deterministic Position Capacity Formula ==="
python -m pytest -q tests/test_milestone_s_pack_7_1_position_ceiling_semantics.py tests/test_milestone_s_pack_7_2_position_capacity_policy.py tests/test_milestone_s_pack_7_3_position_capacity_formula.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Deterministic position capacity formula validation passed."
