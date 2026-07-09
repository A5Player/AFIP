"""Production readiness runtime for Milestone H Pack 10.

This module prepares AFIP for VPS deployment, walk-forward, research,
paper trading, and demo trading without enabling live execution.
"""

from __future__ import annotations

from typing import Any, Mapping

from afip.dashboard_intelligence import DashboardIntelligenceRuntime
from afip.dashboard_center import DashboardRuntimeStatus
from afip.paper_trading import PaperTradingEngineRuntime
from afip.research_center import ResearchCenterRuntime

from .models import DemoTradingReadiness, DeploymentStep, ProductionReadinessReport

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
_ALLOWED_DEMO_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "DEMO", "DEMO_TRADING", "LOCKED_SIMULATION_ONLY"}


def _text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _text(value, default).upper()


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "ready", "completed"}


def _step(step_id: str, en: str, th: str, status: str, reason: str, required: bool = True) -> DeploymentStep:
    return DeploymentStep(step_id, en, th, status, reason, required, True)


class ProductionReadinessRuntime:
    """Validate final Milestone H readiness without changing trading logic."""

    def evaluate_one(self, record: Mapping[str, Any]) -> ProductionReadinessReport:
        broker = _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        profile_name = _text(record.get("profile_name", "Balanced"), "Balanced")
        mode = _upper(record.get("mode", record.get("execution_mode", "DEMO")), "DEMO")
        live_requested = _bool(record.get("live_execution_enabled", False)) or mode == "LIVE"

        validation_items: list[str] = []
        if broker != VERSION1_BROKER:
            validation_items.append("version1_xm_only_required")
        if symbol != VERSION1_SYMBOL:
            validation_items.append("version1_gold_only_required")
        if live_requested:
            validation_items.append("live_execution_blocked_for_pack_10")
        if mode not in _ALLOWED_DEMO_MODES:
            validation_items.append("pack_10_allows_simulation_paper_or_demo_only")

        vps_ready = _bool(record.get("vps_ready", record.get("windows_vps_ready", False)))
        historical_ready = _bool(record.get("historical_data_ready", record.get("historical_research_ready", False)))
        walk_forward_ready = _bool(record.get("walk_forward_ready", False))
        research_ready = ResearchCenterRuntime().evaluate_one(record).status == "READY" or _bool(record.get("research_ready", False))
        paper_ready = PaperTradingEngineRuntime().evaluate_one(record).status in {"READY", "WAITING"} and _bool(record.get("paper_trading_requested", True), True)
        dashboard_ready = DashboardRuntimeStatus().evaluate_one(record).status in {"READY", "WAITING"} and DashboardIntelligenceRuntime().evaluate_one(record).status in {"READY", "WAITING"}
        demo_requested = _bool(record.get("demo_trading_requested", mode in {"DEMO", "DEMO_TRADING"}), mode in {"DEMO", "DEMO_TRADING"})
        demo_terminal_ready = _bool(record.get("mt5_status", "CONNECTED") == "CONNECTED") or _upper(record.get("mt5_status", "")) == "CONNECTED"
        demo_connection_ready = _upper(record.get("broker_status", "XM_READY"), "XM_READY") in {"XM_READY", "CONNECTED", "READY"}
        demo_core_ready = demo_requested and demo_terminal_ready and demo_connection_ready and dashboard_ready and paper_ready

        demo_validation: list[str] = []
        if not demo_requested:
            demo_validation.append("demo_trading_not_requested")
        if not demo_terminal_ready:
            demo_validation.append("mt5_connection_required_for_demo")
        if not demo_connection_ready:
            demo_validation.append("broker_connection_required_for_demo")
        if validation_items:
            demo_validation.extend(validation_items)
        demo_status = "BLOCKED" if validation_items else ("READY" if demo_core_ready else "WAITING")
        demo_reason = "demo_trading_ready_without_live_execution" if demo_status == "READY" else ("demo_trading_blocked_by_policy" if demo_status == "BLOCKED" else "demo_trading_waiting_for_runtime_prerequisites")
        demo = DemoTradingReadiness(demo_status, broker, symbol, profile_name, "DEMO", True if demo_status == "READY" else False, False, demo_reason, tuple(demo_validation))

        steps = (
            _step("vps_deployment", "Windows VPS Deployment", "ติดตั้งบน Windows VPS", "READY" if vps_ready else "WAITING", "vps_ready" if vps_ready else "vps_setup_required"),
            _step("historical_download", "Historical Data Download", "ดาวน์โหลดข้อมูลย้อนหลัง", "READY" if historical_ready else "WAITING", "historical_data_ready" if historical_ready else "historical_data_required"),
            _step("walk_forward", "Walk Forward Validation", "ทดสอบ Walk Forward", "READY" if walk_forward_ready else "WAITING", "walk_forward_ready" if walk_forward_ready else "walk_forward_required"),
            _step("research", "Research Center", "ศูนย์วิจัย", "READY" if research_ready else "WAITING", "research_ready" if research_ready else "research_dataset_required"),
            _step("paper_trading", "Paper Trading", "เทรดจำลอง", "READY" if paper_ready else "WAITING", "paper_trading_ready" if paper_ready else "paper_trading_required"),
            _step("dashboard", "Dashboard", "แดชบอร์ด", "READY" if dashboard_ready else "WAITING", "dashboard_ready" if dashboard_ready else "dashboard_runtime_required"),
            _step("demo_trading", "Demo Trading", "เทรดบัญชีทดลอง", demo.status, demo.reason),
            _step("live_trading", "Live Trading", "เทรดเงินจริง", "BLOCKED", "live_trading_not_enabled_in_milestone_h_pack_10"),
        )

        if validation_items:
            status, reason, stage = "BLOCKED", "production_readiness_blocked_by_version1_or_live_policy", "PACK_10_BLOCKED"
        elif all((vps_ready, historical_ready, walk_forward_ready, research_ready, paper_ready, dashboard_ready, demo.status == "READY")):
            status, reason, stage = "READY", "milestone_h_pack_10_release_candidate_ready_for_vps_demo_workflow", "VERSION_1_RELEASE_CANDIDATE"
        else:
            status, reason, stage = "WAITING", "production_readiness_waiting_for_required_workflow", "PACK_10_WAITING"

        return ProductionReadinessReport(
            status=status,
            reason=reason,
            release_stage=stage,
            broker=broker,
            symbol=symbol,
            profile_name=profile_name,
            vps_ready=vps_ready,
            historical_data_ready=historical_ready,
            walk_forward_ready=walk_forward_ready,
            research_ready=research_ready,
            paper_trading_ready=paper_ready,
            dashboard_ready=dashboard_ready,
            demo_trading_ready=demo.status == "READY",
            live_execution_enabled=False,
            trading_logic_changed=False,
            deployment_steps=steps,
            demo_readiness=demo,
            dashboard_sections=("Runtime", "Intelligence", "Order Center", "AFIP Bank", "Research", "System", "Market", "Production Readiness"),
            handoff_items=("deploy_to_vps", "download_historical_data", "run_walk_forward", "run_research", "run_paper_trading", "run_demo_trading", "do_not_enable_live_trading"),
            validation_items=tuple(validation_items),
        )

    def explain_one(self, record: Mapping[str, Any]) -> ProductionReadinessReport:
        return self.evaluate_one(record)
