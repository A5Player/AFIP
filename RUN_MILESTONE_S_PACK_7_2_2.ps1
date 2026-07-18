$ErrorActionPreference = "Stop"

Write-Host "=== AFIP Milestone S Pack 7.2.2 - P2 Position Limit Validation ==="

python -m pytest -q tests/test_milestone_s_pack_7_2_position_capacity_policy.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

python tools/validate_financial_naming.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "P2 position limit validation passed."
