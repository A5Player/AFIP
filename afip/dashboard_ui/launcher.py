"""Dashboard UI launcher for Pack 8."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .runtime import DashboardUIRuntime


def default_dashboard_record() -> dict[str, Any]:
    return {
        "broker": "XM",
        "symbol": "GOLD#",
        "profile_name": "Balanced",
        "mode": "DEMO",
        "execution_mode": "DEMO",
        "production_readiness_requested": True,
        "demo_trading_requested": True,
        "vps_ready": True,
        "windows_vps_ready": True,
        "market_regime": "TRENDING",
        "paper_trading_requested": True,
        "paper_balance": 1000,
        "reserve": 200,
        "maximum_units": 3,
        "research_center_requested": True,
        "historical_dataset_ready": True,
        "historical_data_ready": True,
        "history_ready": True,
        "historical_research_ready": True,
        "walk_forward_ready": True,
        "connection_test_passed": True,
        "saved": True,
        "login": "configured",
        "password": "configured",
        "mt5_terminal_path": "configured",
        "completed_research_orders": 120,
        "paper_orders": [
            {
                "order_id": "PAPER-DEMO-1",
                "side": "BUY",
                "units": 1,
                "status": "MANAGING",
                "entry_price": 2300,
                "current_price": 2303,
                "confidence": 82,
                "risk_status": "risk_pass",
                "reason": "paper_dashboard_sample_holding_reason",
            }
        ],
    }


def launch_dashboard(output_path: str | Path = "runtime/dashboard/afip_dashboard.html", record: dict[str, Any] | None = None) -> Path:
    return DashboardUIRuntime().write_html(record or default_dashboard_record(), output_path)
