from pathlib import Path
import json

from afip.capital_growth_engine import CapitalGrowthEngine
from afip.four_profile_operations.runtime import ProfileOperationalConfig
from afip.position_capacity_formula import capital_tiers_from_profile

CONFIG = Path(__file__).resolve().parents[1] / "config" / "four_profile_demo.json"

def _profiles():
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    return {item["profile_id"]: item for item in payload["profiles"]}

def test_profile_operational_config_remains_backward_compatible():
    fields = ProfileOperationalConfig.__dataclass_fields__
    assert fields["execution_enabled"].default is True
    assert fields["research_enabled"].default is True

def test_p1_to_p3_use_tier_table_as_only_declared_sizing_authority():
    profiles = _profiles()
    for pid in ("P1", "P2", "P3"):
        assert profiles[pid]["execution_enabled"] is True
        assert profiles[pid]["allocation_mode"] == "CAPITAL_TIER_TABLE"
        assert profiles[pid]["sizing_authority"] == "CAPITAL_TIER_FORMULA_ONLY"
        assert "capital_per_unit" not in profiles[pid]
        assert "capital_per_unit_legacy_only" not in profiles[pid]

def test_latest_approved_balance_curves_are_preserved():
    profiles = _profiles()
    p1 = capital_tiers_from_profile(profiles["P1"])
    p2 = capital_tiers_from_profile(profiles["P2"])
    p3 = capital_tiers_from_profile(profiles["P3"])
    assert p1[:4] == ((0, (0.01,)), (300, (0.01, 0.01)), (900, (0.01, 0.01, 0.01)), (1800, (0.02, 0.02, 0.02)))
    assert p1[-1] == (19800, (0.10, 0.10, 0.10))
    assert p2[-1] == (1545300, (1.0, 1.0, 1.0))
    assert p3[:4] == ((0, (0.01,)), (200, (0.01, 0.01)), (450, (0.01, 0.01, 0.01)), (1200, (0.02, 0.02, 0.02)))
    assert p3[-1] == (600000, (10.0, 10.0, 10.0))

def test_tier_mode_never_depends_on_legacy_capital_per_unit():
    p1 = _profiles()["P1"]
    decision = CapitalGrowthEngine.evaluate(
        mode="CAPITAL_TIER_TABLE", balance=900, current_orders=0,
        capital_tiers=capital_tiers_from_profile(p1), maximum_orders=3,
        legacy_capital_per_unit=0, legacy_maximum_units=0,
    )
    assert decision.available_lots == (0.01, 0.01, 0.01)

def test_invalid_legacy_capital_fails_closed_without_zero_division():
    decision = CapitalGrowthEngine.evaluate(
        mode="LEGACY_FIXED_UNIT", balance=1000, current_orders=0,
        legacy_capital_per_unit=0, legacy_maximum_units=3,
    )
    assert decision.available_lots == ()
