from __future__ import annotations

from pathlib import Path

from afip.demo_execution_gateway.runtime import DemoExecutionGateway, DemoProfilePolicy
from afip.four_profile_operations.runtime import ProfileOperationalConfig


def _profile(tmp_path: Path) -> ProfileOperationalConfig:
    terminal = tmp_path / "terminal64.exe"
    terminal.write_text("", encoding="utf-8")
    return ProfileOperationalConfig(
        profile_id="P1", profile_name="High Safety", enabled=True, launch_mt5=False,
        mt5_folder=tmp_path, mt5_terminal=terminal, broker="XM", server="XMGlobal-MT5 6",
        symbol="GOLD#", login_env="AFIP_P1_LOGIN", password_env="AFIP_P1_PASSWORD",
        runtime_directory=tmp_path / "runtime", database_path=tmp_path / "database" / "afip.sqlite3",
        logs_directory=tmp_path / "logs", dashboard_path=tmp_path / "dashboard" / "index.html",
        learning_directory=tmp_path / "learning", knowledge_directory=tmp_path / "knowledge",
        statistics_directory=tmp_path / "statistics",
    )


def _policy() -> DemoProfilePolicy:
    return DemoProfilePolicy.from_mapping({
        "profile_id": "P1", "enabled": True, "execution_enabled": True,
        "demo_execution_enabled": True, "maximum_units": 3,
        "minimum_confidence": 98, "minimum_seconds_between_entries": 900,
        "magic": 26071001, "lot_per_unit": 0.01,
        "allocation_mode": "CAPITAL_TIER_TABLE", "maximum_concurrent_orders": 3,
        "maximum_lot_per_order": 0.01,
        "capital_tiers": [{"minimum_balance": 0, "lots": [0.01, 0.01, 0.01]}],
    })


def _runtime_result() -> dict:
    return {
        "symbol": "GOLD#",
        "data_status": "READY",
        "data_source": "MT5_OHLC",
        "primary_timeframe": "H1",
        "modular_intelligence": {
            "market_regime": {"market_regime": "TRENDING", "confidence": 91.0},
            "pattern": {"pattern_name": "BREAKOUT", "direction": "BUY", "score": 88.0},
        },
        "multi_timeframe_confluence": {
            "status": "READY", "primary_timeframe": "H1", "direction": "BUY", "score": 92.0,
        },
        "decision": {"action": "BUY", "confidence": 99.0, "score": 94.0, "reason": "confluence_pass"},
        "confidence_calibration": {"status": "READY", "raw_confidence": 97.0, "calibrated_confidence": 99.0},
        "risk": {"allowed": True, "status": "PASS", "reasons": ["risk_pass"]},
        "trading_cost_intelligence": {
            "status": "PASS", "allowed": True, "spread_points": 18.0,
            "caution_spread_points": 25.0, "max_spread_points": 35.0,
        },
        "order": {
            "status": "SIMULATION_ORDER_READY", "action": "BUY",
            "protection": {
                "stop_loss_points": 1200.0, "take_profit_points": 2400.0,
                "risk_reward_ratio": 2.0, "stop_loss_source": "ATR_STRUCTURE",
                "take_profit_source": "RR_AUTHORITY",
            },
        },
    }


def test_intelligence_snapshot_covers_decision_authority_chain():
    snapshot = DemoExecutionGateway._intelligence_snapshot(_runtime_result())

    assert snapshot["data"]["source"] == "MT5_OHLC"
    assert snapshot["market_regime"]["market_regime"] == "TRENDING"
    assert snapshot["pattern"]["pattern_name"] == "BREAKOUT"
    assert snapshot["confluence"]["direction"] == "BUY"
    assert snapshot["decision"]["confidence"] == 99.0
    assert snapshot["risk"]["allowed"] is True
    assert snapshot["sl_tp"]["stop_loss_points"] == 1200.0
    assert snapshot["sl_tp"]["take_profit_source"] == "RR_AUTHORITY"
    assert snapshot["trading_cost"]["status"] == "PASS"


def test_decision_pipeline_is_ordered_and_only_uses_available_stages():
    snapshot = DemoExecutionGateway._intelligence_snapshot(_runtime_result())

    assert DemoExecutionGateway._decision_pipeline(snapshot) == (
        "MARKET_DATA", "MARKET_REGIME", "PATTERN_INTELLIGENCE",
        "MULTI_TIMEFRAME_CONFLUENCE", "DECISION_INTELLIGENCE",
        "CONFIDENCE_CALIBRATION", "RISK_AUTHORITY", "SL_TP_AUTHORITY",
        "TRADING_COST_AUTHORITY", "EXECUTION_READINESS",
    )


def test_report_persists_intelligence_snapshot_under_same_trace(tmp_path):
    gateway = DemoExecutionGateway(_profile(tmp_path), _policy(), mt5=object())
    gateway._active_trace_id = "AFIP-P1-CERTIFICATION"
    gateway._active_intelligence_snapshot = gateway._intelligence_snapshot(_runtime_result())

    report = gateway._report(
        "WAITING", "profile_order_capacity_unavailable",
        decision_action="BUY", decision_confidence=99.0,
    )

    assert report.execution_trace_id == "AFIP-P1-CERTIFICATION"
    assert report.intelligence_snapshot["decision"]["action"] == "BUY"
    assert report.decision_pipeline[0] == "MARKET_DATA"
    assert report.decision_pipeline[-1] == "EXECUTION_READINESS"
    assert report.authority_snapshot["decision_action"] == "BUY"
