"""Dashboard intelligence integration runtime for Production Milestone H Pack 9."""

from __future__ import annotations

from typing import Any, Mapping

from afip.dashboard_center import DashboardRuntimeStatus
from afip.historical_data_manager import HistoricalDataDownloadPipeline, HistoricalDataManagerRuntime
from afip.paper_trading import PaperTradingEngineRuntime
from afip.profile_manager import ProfileManagerRuntime
from afip.research_center import ResearchCenterRuntime
from afip.runtime_service_manager import RuntimeServiceManager

from .models import DashboardDecisionExplanation, DashboardEngineRow, DashboardIntelligenceReport

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
_ALLOWED_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}


def _text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _text(value, default).upper()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _status_icon(status: str) -> str:
    status = _upper(status, "READY")
    if status == "READY":
        return "✅"
    if status in {"WAITING", "REVIEW", "RECOVERING"}:
        return "⏳"
    if status == "BLOCKED":
        return "⛔"
    return "ℹ️"


class DashboardIntelligenceRuntime:
    """Build one dashboard-ready intelligence report from existing Pack 1-8 runtimes."""

    def evaluate_one(self, record: Mapping[str, Any]) -> DashboardIntelligenceReport:
        data = dict(record)
        broker = _upper(data.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(data.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        mode = _upper(data.get("mode", data.get("execution_mode", "PAPER")), "PAPER")
        profile_name = _text(data.get("profile_name", "Balanced"), "Balanced")

        dashboard_runtime = DashboardRuntimeStatus().evaluate_one(data)
        runtime_service = RuntimeServiceManager().evaluate_one(data)
        profile = ProfileManagerRuntime().evaluate_one(data)
        history = HistoricalDataManagerRuntime().evaluate_one(data)
        historical_download = HistoricalDataDownloadPipeline().evaluate_one(data)
        research = ResearchCenterRuntime().evaluate_one(data)
        paper = PaperTradingEngineRuntime().evaluate_one(data)

        validation_items: list[str] = []
        if broker != VERSION1_BROKER:
            validation_items.append("version1_xm_only_required")
        if symbol != VERSION1_SYMBOL:
            validation_items.append("version1_gold_only_required")
        if mode == "LIVE" or bool(data.get("live_execution_enabled", False)):
            validation_items.append("live_execution_blocked_for_dashboard_intelligence")
        if mode not in _ALLOWED_MODES:
            validation_items.append("dashboard_intelligence_allows_simulation_or_paper_only")

        engine_rows = (
            _row("Runtime Service Manager", "ตัวจัดการ Runtime", "VPS runtime, recovery, heartbeat, and event history.", "VPS and connection state", runtime_service.reason, runtime_service.status, data),
            _row("Profile Manager", "ตัวจัดการโปรไฟล์", "Trading policy profile separated from account and MT5 endpoint.", "Profile configuration", profile.reason, profile.status, data),
            _row("Historical Data Manager", "ตัวจัดการข้อมูลย้อนหลัง", "Historical readiness, quality, missing bars, and walk forward support.", "MT5 OHLC history", history.reason, history.status, data),
            _row("Historical Download Pipeline", "กระบวนการดาวน์โหลดข้อมูลย้อนหลัง", "Download quality validation for research and walk forward datasets.", "XM GOLD# timeframes", historical_download.reason, historical_download.status, data),
            _row("Research Center", "ศูนย์วิจัย", "Separated research statistics, live statistics, and standard learning readiness.", "Research-only completed orders", research.reason, research.status, data, research_scope=research.research_scope, live_scope=research.live_scope),
            _row("Paper Trading Engine", "ระบบเทรดจำลอง", "Paper order lifecycle, unit allocation, explainability, and AFIP Bank values.", "Paper order context", paper.reason, paper.status, data),
        )
        explanation = _decision_explanation(paper, data)
        if validation_items:
            status, reason = "BLOCKED", "dashboard_intelligence_blocked_by_version1_or_live_policy"
        elif dashboard_runtime.status == "BLOCKED" or any(row.status == "BLOCKED" for row in engine_rows):
            status, reason = "BLOCKED", "dashboard_intelligence_blocked_by_dependency"
        elif dashboard_runtime.status in {"WAITING", "REVIEW", "RECOVERING"} or any(row.status in {"WAITING", "REVIEW", "RECOVERING"} for row in engine_rows):
            status, reason = "WAITING", "dashboard_intelligence_waiting_for_dependency"
        else:
            status, reason = "READY", "dashboard_intelligence_integrated_runtime_ready"
        order_statuses = tuple(order.status for order in paper.orders) or ("WAITING",)
        sections = ("runtime", "intelligence", "engine", "trading", "analytics", "afip_bank", "research", "system", "market", "order_center", "explainability")
        return DashboardIntelligenceReport(
            status=status,
            reason=reason,
            broker=broker,
            symbol=symbol,
            profile_name=profile_name,
            mode=mode,
            runtime_status=runtime_service.status,
            profile_status=profile.status,
            research_center_status=research.status,
            paper_trading_status=paper.status,
            afip_bank_status=paper.status,
            historical_data_status=history.status,
            market_status=_text(data.get("market_status", "market_status_pending_live_calendar"), "market_status_pending_live_calendar"),
            engine_rows=engine_rows,
            decision_explanation=explanation,
            research_statistics_scope=research.research_scope,
            live_statistics_scope=research.live_scope,
            order_center_statuses=order_statuses,
            dashboard_sections=sections,
            validation_items=tuple(validation_items),
        )

    def explain_one(self, record: Mapping[str, Any]) -> DashboardIntelligenceReport:
        return self.evaluate_one(record)


def _row(name_en: str, name_th: str, description: str, input_text: str, output: str, status: str, record: Mapping[str, Any], *, research_scope: str = "RESEARCH_SEPARATE", live_scope: str = "LIVE_SEPARATE") -> DashboardEngineRow:
    confidence = round(_float(record.get("confidence", record.get("ai_confidence", 0.0)), 0.0), 2)
    accuracy = round(_float(record.get("accuracy", record.get("research_accuracy", 0.0)), 0.0), 2)
    win_rate = round(_float(record.get("win_rate", record.get("research_win_rate", 0.0)), 0.0), 2)
    return DashboardEngineRow(
        english_name=name_en,
        thai_name=name_th,
        description=description,
        input=input_text,
        output=_text(output, "runtime_output_pending"),
        status_icon=_status_icon(status),
        status=_upper(status, "READY"),
        confidence=confidence,
        accuracy=accuracy,
        win_rate=win_rate,
        runtime=_text(record.get("runtime", record.get("runtime_seconds", "runtime_cycle")), "runtime_cycle"),
        waiting_reason=_text(record.get("waiting_reason", "no_waiting_reason"), "no_waiting_reason"),
        dependency=_text(record.get("dependency", "dashboard_runtime_dependency"), "dashboard_runtime_dependency"),
        health=_text(record.get("health", status), status),
        research_statistics=research_scope,
        live_statistics=live_scope,
    )


def _decision_explanation(paper: Any, record: Mapping[str, Any]) -> DashboardDecisionExplanation:
    order = paper.orders[0] if paper.orders else None
    return DashboardDecisionExplanation(
        waiting_reason=_text(getattr(order, "waiting_reason", None), _text(record.get("waiting_reason", "waiting_for_complete_runtime_review"), "waiting_for_complete_runtime_review")),
        entry_reason=_text(getattr(order, "entry_reason", None), "entry_requires_policy_risk_and_market_regime_alignment"),
        holding_reason=_text(getattr(order, "holding_reason", None), "hold_while_market_reason_and_risk_remain_valid"),
        stop_loss_reason=_text(getattr(order, "stop_loss_reason", None), "stop_loss_review_protects_capital_per_profile_risk"),
        break_even_reason=_text(getattr(order, "break_even_reason", None), "break_even_only_after_protection_condition_is_met"),
        trailing_reason=_text(getattr(order, "trailing_reason", None), "trailing_only_after_profit_protection_is_justified"),
        partial_close_reason=_text(getattr(order, "partial_close_reason", None), "partial_close_uses_units_not_direct_lot_increase"),
        exit_reason=_text(getattr(order, "exit_reason", None), "exit_waits_for_complete_exit_reason"),
        rejected_entry_reason=_text(record.get("rejected_entry_reason", "rejected_entry_waits_for_policy_alignment"), "rejected_entry_waits_for_policy_alignment"),
        rejected_exit_reason=_text(record.get("rejected_exit_reason", "rejected_exit_waits_for_complete_exit_evidence"), "rejected_exit_waits_for_complete_exit_evidence"),
        alternative_decision=_text(getattr(order, "alternative_decision", None), "wait_and_reassess"),
        current_ai_reasoning=_text(getattr(order, "current_ai_reasoning", None), _text(record.get("current_ai_reasoning", "dashboard_intelligence_reviewing_current_context"), "dashboard_intelligence_reviewing_current_context")),
        expected_next_action=_text(getattr(order, "expected_next_action", None), "continue_dashboard_runtime_review"),
        risk_status=_text(getattr(order, "risk_status", None), _text(record.get("risk_status", "risk_review"), "risk_review")),
        estimated_next_review=_text(getattr(order, "estimated_next_review", None), "next_runtime_cycle"),
    )
