import json
from pathlib import Path

from afip.demo_execution_gateway.runtime import DemoProfilePolicy

CONFIG = Path(__file__).resolve().parents[1] / "config" / "four_profile_demo.json"


def profiles():
    data=json.loads(CONFIG.read_text(encoding="utf-8"))
    expanded = {}
    for raw in data["profiles"]:
        item = dict(raw)
        policy = DemoProfilePolicy.from_mapping(raw)
        item["capital_tiers"] = [
            {"minimum_balance": level, "lots": list(lots)}
            for level, lots in policy.capital_tiers
        ]
        expanded[item["profile_id"]] = item
    return data, expanded


def tier_map(profile):
    return {x["minimum_balance"]:x["lots"] for x in profile["capital_tiers"]}


def test_policy_version_and_guide_are_declared():
    data,_=profiles()
    assert data["position_policy"]["version"] == "AFIP_POSITION_POLICY_V2_1"
    assert data["position_policy"]["data_guide"].endswith("AFIP_POSITION_CAPACITY_AND_SCORING_DATA_GUIDE_V2_1.md")


def test_p1_latest_capacity_curve():
    _,p=profiles(); m=tier_map(p["P1"])
    assert m[0] == [0.01]
    assert m[300] == [0.01,0.01]
    assert m[900] == [0.01,0.01,0.01]
    assert m[1800] == [0.02]*3
    assert m[19800] == [0.1]*3
    assert len(p["P1"]["capital_tiers"]) == 12
    assert p["P1"]["maximum_lot_per_order"] == 0.1


def test_p2_latest_capacity_curve_and_ceiling():
    _,p=profiles(); tiers=p["P2"]["capital_tiers"]; m=tier_map(p["P2"])
    assert m[0] == [0.01]
    assert m[300] == [0.01,0.01]
    assert m[900] == [0.01]*3
    assert m[1800] == [0.02]*3
    assert m[19800] == [0.1]*3
    assert m[23400] == [0.11]*3
    assert tiers[-1]["minimum_balance"] == 1545300
    assert tiers[-1]["lots"] == [1.0]*3
    assert p["P2"]["maximum_lot_per_order"] == 1.0
    assert max(max(tier["lots"]) for tier in tiers) == 1.0
    assert all(max(tier["lots"]) <= 1.0 for tier in tiers)
    assert not any(any(lot > 1.0 for lot in tier["lots"]) for tier in tiers)


def test_p3_latest_capacity_curve_and_ceiling():
    _,p=profiles(); tiers=p["P3"]["capital_tiers"]; m=tier_map(p["P3"])
    assert m[0] == [0.01]
    assert m[200] == [0.01,0.01]
    assert m[450] == [0.01]*3
    assert m[1200] == [0.02]*3
    assert m[1800] == [0.03]*3
    assert m[3000] == [0.05]*3
    assert tiers[-1]["minimum_balance"] == 600000
    assert tiers[-1]["lots"] == [10.0]*3
    assert p["P3"]["maximum_lot_per_order"] == 10.0


def test_p4_remains_fixed_research_001():
    _,p=profiles(); p4=p["P4"]
    assert p4["allocation_mode"] == "RESEARCH_FIXED_001"
    assert p4["maximum_lot_per_order"] == 0.01
    assert p4["capital_tiers"] == []
