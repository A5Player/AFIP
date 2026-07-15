from pathlib import Path

from afip.demo_execution_gateway.runtime import DemoExecutionGateway, DemoProfilePolicy
from afip.four_profile_operations.runtime import ProfileOperationalConfig


def _profile(tmp_path: Path, profile_id: str = "P1") -> ProfileOperationalConfig:
    terminal = tmp_path / "terminal64.exe"
    terminal.write_text("", encoding="utf-8")
    return ProfileOperationalConfig(
        profile_id=profile_id, profile_name="Test", enabled=True, launch_mt5=False,
        mt5_folder=tmp_path, mt5_terminal=terminal, broker="XM", server="XMGlobal-MT5 6",
        symbol="GOLD#", login_env=f"AFIP_{profile_id}_LOGIN", password_env=f"AFIP_{profile_id}_PASSWORD",
        runtime_directory=tmp_path / "runtime", database_path=tmp_path / "db.sqlite3",
        logs_directory=tmp_path / "logs", dashboard_path=tmp_path / "dashboard.html",
        learning_directory=tmp_path / "learning", knowledge_directory=tmp_path / "knowledge",
        statistics_directory=tmp_path / "statistics",
    )


def _policy(profile_id: str, tiers):
    return DemoProfilePolicy.from_mapping({
        "profile_id": profile_id,
        "enabled": True,
        "demo_execution_enabled": True,
        "capital_per_unit": 1,
        "maximum_units": 4,
        "minimum_confidence": 98 if profile_id == "P1" else 95,
        "minimum_seconds_between_entries": 900,
        "magic": 26071001,
        "lot_per_unit": 0.01,
        "allocation_mode": "CAPITAL_TIER_TABLE",
        "maximum_concurrent_orders": 4,
        "maximum_lot_per_order": 0.03,
        "capital_tiers": [
            {"minimum_balance": balance, "lots": lots}
            for balance, lots in tiers
        ],
    })


P1 = [
    (0, [.01]), (200, [.01, .01]), (450, [.01, .01, .01]),
    (800, [.01, .01, .01, .01]), (1250, [.02, .01, .01, .01]),
    (1800, [.02, .02, .01, .01]), (2450, [.02, .02, .02, .01]),
    (3200, [.02, .02, .02, .02]), (4050, [.03, .02, .02, .02]),
    (5000, [.03, .03, .02, .02]), (6050, [.03, .03, .03, .02]),
    (7200, [.03, .03, .03, .03]),
]
P2 = [
    (0, [.01]), (300, [.01, .01]), (600, [.01, .01, .01]),
    (1000, [.01, .01, .01, .01]), (1500, [.02, .01, .01, .01]),
    (2100, [.02, .02, .01, .01]), (2800, [.02, .02, .02, .01]),
    (3600, [.02, .02, .02, .02]), (4500, [.03, .02, .02, .02]),
    (5500, [.03, .03, .02, .02]), (6600, [.03, .03, .03, .02]),
    (7800, [.03, .03, .03, .03]),
]


def test_p1_capital_tiers_match_approved_schedule(tmp_path):
    gateway = DemoExecutionGateway(_profile(tmp_path), _policy("P1", P1))
    assert gateway._allocation_lots(100, 0) == (.01,)
    assert gateway._allocation_lots(200, 0) == (.01, .01)
    assert gateway._allocation_lots(1250, 0) == (.02, .01, .01, .01)
    assert gateway._allocation_lots(5000, 0) == (.03, .03, .02, .02)
    assert gateway._allocation_lots(7200, 0) == (.03, .03, .03, .03)
    assert gateway._allocation_lots(100000, 0) == (.03, .03, .03, .03)


def test_p2_capital_tiers_match_approved_schedule(tmp_path):
    gateway = DemoExecutionGateway(_profile(tmp_path, "P2"), _policy("P2", P2))
    assert gateway._allocation_lots(100, 0) == (.01,)
    assert gateway._allocation_lots(300, 0) == (.01, .01)
    assert gateway._allocation_lots(1500, 0) == (.02, .01, .01, .01)
    assert gateway._allocation_lots(5500, 0) == (.03, .03, .02, .02)
    assert gateway._allocation_lots(7800, 0) == (.03, .03, .03, .03)


def test_existing_orders_only_fill_remaining_tier_slots(tmp_path):
    gateway = DemoExecutionGateway(_profile(tmp_path), _policy("P1", P1))
    assert gateway._allocation_lots(1250, 2) == (.01, .01)
    assert gateway._allocation_lots(1250, 4) == ()


def test_research_profiles_keep_one_fixed_001_order_per_approved_signal(tmp_path):
    policy = DemoProfilePolicy.from_mapping({
        "profile_id": "P3", "enabled": True, "demo_execution_enabled": True,
        "capital_per_unit": 1, "maximum_units": 1, "minimum_confidence": 90,
        "minimum_seconds_between_entries": 900, "magic": 26071003,
        "lot_per_unit": .01, "allocation_mode": "RESEARCH_FIXED_001",
        "maximum_concurrent_orders": 0, "maximum_lot_per_order": .01,
    })
    gateway = DemoExecutionGateway(_profile(tmp_path, "P3"), policy)
    assert policy.validate() == ()
    assert gateway._allocation_lots(100, 250) == (.01,)
