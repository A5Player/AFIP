param(
    [string]$ProjectRoot = "C:\AFIP\source"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . ".\.venv\Scripts\Activate.ps1"
}

python -m pytest `
    tests\test_afip_final_capital_tier_authority.py `
    tests\test_milestone_s_pack_7_3_position_capacity_formula.py `
    tests\test_afip_account_isolation_capital_safety.py `
    -q

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python - <<'PY'
import json
from pathlib import Path
from afip.lot_authority import calculate_lot_authority

profiles = {p["profile_id"]: p for p in json.loads(Path("config/four_profile_demo.json").read_text(encoding="utf-8"))["profiles"]}
cases = [
    ("P1", 299, 1, 0.01), ("P1", 300, 2, 0.01), ("P1", 900, 3, 0.01),
    ("P1", 1800, 3, 0.02), ("P1", 19800, 3, 0.10),
    ("P2", 299, 1, 0.01), ("P2", 300, 2, 0.01), ("P2", 900, 3, 0.01),
    ("P3", 199, 1, 0.01), ("P3", 200, 2, 0.01), ("P3", 450, 3, 0.01),
    ("P3", 1200, 3, 0.02), ("P4", 999999, 1, 0.01),
]
for pid, balance, expected_units, expected_lot in cases:
    r = calculate_lot_authority(profile=profiles[pid], decision={"requested_units": 3}, confidence=100.0, balance=balance, equity=balance)
    assert (r.approved_units, r.approved_lot_per_order) == (expected_units, expected_lot), (pid, balance, r)
print("AFIP Maximum Lot Authority certification: PASS")
PY
