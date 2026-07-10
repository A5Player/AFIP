"""Visible Dashboard UI runtime for Production Milestone H Pack 8."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Mapping

from afip.dashboard_center import DashboardFoundationRuntime, DashboardRuntimeStatus
from afip.dashboard_intelligence import DashboardIntelligenceRuntime
from afip.paper_trading import PaperTradingEngineRuntime
from afip.research_center import ResearchCenterRuntime
from afip.production_readiness import ProductionReadinessRuntime
from afip.vps_health_monitor import VPSHealthMonitorRuntime
from afip.mt5_live_account import MT5LiveAccountRuntime
from afip.internet_monitor import InternetMonitorRuntime
from afip.market_calendar import MarketCalendarRuntime
from afip.explainable_order_center import ExplainableOrderCenterRuntime
from afip.afip_bank_live import AFIPBankLiveRuntime
from afip.historical_data_manager import HistoricalDataLiveRuntime
from afip.dashboard_live_runtime import DashboardLiveRuntime
from afip.runtime_supervisor import RuntimeSupervisorRuntime
from afip.production_certification import ProductionCertificationRuntime
from afip.profile_customization import ProfileCustomizationRuntime
from afip.economic_calendar_intelligence import EconomicCalendarIntelligenceRuntime
from afip.news_intelligence import NewsIntelligenceRuntime
from afip.gold_macro_intelligence import GoldMacroIntelligenceRuntime
from afip.central_bank_intelligence import CentralBankIntelligenceRuntime
from afip.cot_intelligence import COTIntelligenceRuntime
from afip.open_interest_intelligence import OpenInterestIntelligenceRuntime
from afip.etf_flow_intelligence import ETFFlowIntelligenceRuntime
from afip.usd_index_intelligence import USDIndexIntelligenceRuntime
from afip.bond_yield_intelligence import BondYieldIntelligenceRuntime
from afip.market_regime_v2 import MarketRegimeV2Runtime
from afip.decision_intelligence_foundation import DecisionIntelligenceFoundationRuntime
from afip.consensus_engine import ConsensusEngineRuntime
from afip.conflict_resolver import ConflictResolverRuntime
from afip.opportunity_ranking import OpportunityRankingRuntime
from afip.trade_scoring import TradeScoringRuntime
from afip.unit_allocation import UnitAllocationRuntime
from afip.entry_validation import EntryValidationRuntime
from afip.exit_validation import ExitValidationRuntime
from afip.portfolio_decision import PortfolioDecisionRuntime
from afip.decision_intelligence_certification import DecisionIntelligenceCertificationRuntime
from afip.execution_intelligence_foundation import ExecutionIntelligenceFoundationRuntime
from afip.smart_entry import SmartEntryRuntime
from afip.smart_exit import SmartExitRuntime
from afip.dynamic_stop_loss import DynamicStopLossRuntime
from afip.dynamic_take_profit import DynamicTakeProfitRuntime

from .models import DashboardPanel, DashboardUIReport


VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
_ALLOWED_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "DEMO", "DEMO_TRADING", "LOCKED_SIMULATION_ONLY"}


def _text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _text(value, default).upper()


class DashboardUIRuntime:
    """Render a visible dashboard from existing AFIP runtime data."""

    def evaluate_one(self, record: Mapping[str, Any]) -> DashboardUIReport:
        broker = _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        mode = _upper(record.get("mode", record.get("execution_mode", "PAPER")), "PAPER")
        profile_name = _text(record.get("profile_name", "Balanced"), "Balanced")
        runtime = DashboardRuntimeStatus().evaluate_one(record)
        foundation = DashboardFoundationRuntime().evaluate_one({**dict(record), "market_regime": record.get("market_regime", "TRENDING"), "execution_mode": mode})
        paper = PaperTradingEngineRuntime().evaluate_one(record)
        research = ResearchCenterRuntime().evaluate_one(record)
        integrated = DashboardIntelligenceRuntime().evaluate_one(record)
        production_requested = bool(record.get("production_readiness_requested", False)) or mode in {"DEMO", "DEMO_TRADING"}
        production = ProductionReadinessRuntime().evaluate_one(record) if production_requested else None
        vps_health = VPSHealthMonitorRuntime().evaluate_one({**dict(record), "mode": mode})
        mt5_account = MT5LiveAccountRuntime().evaluate_one({**dict(record), "mode": mode})
        internet = InternetMonitorRuntime().evaluate_one({**dict(record), "mode": mode})
        market_calendar = MarketCalendarRuntime().evaluate_one({**dict(record), "mode": mode})
        explainable_orders = ExplainableOrderCenterRuntime().evaluate_one({**dict(record), "mode": mode})
        afip_bank = AFIPBankLiveRuntime().evaluate_one({**dict(record), "mode": mode, "closed_profit": paper.closed_profit, "floating_profit": paper.floating_profit})
        historical_data = HistoricalDataLiveRuntime().evaluate_one({**dict(record), "mode": mode})
        dashboard_live = DashboardLiveRuntime().evaluate_one({**dict(record), "mode": mode})
        runtime_supervisor = RuntimeSupervisorRuntime().evaluate_one({**dict(record), "mode": mode})
        production_certification = ProductionCertificationRuntime().evaluate_one({**dict(record), "mode": mode})
        profile_customization = ProfileCustomizationRuntime(record.get("profile_storage_path", "runtime/profiles/profiles.json")).preview(record)
        economic_calendar = EconomicCalendarIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        news_intelligence = NewsIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        gold_macro = GoldMacroIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        central_bank = CentralBankIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        cot_intelligence = COTIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        open_interest_intelligence = OpenInterestIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        etf_flow_intelligence = ETFFlowIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        usd_index_intelligence = USDIndexIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        bond_yield_intelligence = BondYieldIntelligenceRuntime().evaluate_one({**dict(record), "mode": mode})
        market_regime_v2 = MarketRegimeV2Runtime().evaluate_one({
            **dict(record), "mode": mode,
            "economic_calendar_status": economic_calendar.status, "economic_calendar_effect": "NEUTRAL", "economic_calendar_score": 0.0, "economic_calendar_confidence": getattr(economic_calendar, "confidence", 0.0),
            "news_status": news_intelligence.status, "news_effect": getattr(news_intelligence, "aggregate_sentiment", "NEUTRAL"), "news_score": getattr(news_intelligence, "aggregate_score", 0.0), "news_confidence": getattr(news_intelligence, "confidence", 0.0),
            "gold_macro_status": gold_macro.status, "gold_macro_effect": getattr(gold_macro, "aggregate_gold_effect", "NEUTRAL"), "gold_macro_score": getattr(gold_macro, "aggregate_score", 0.0), "gold_macro_confidence": getattr(gold_macro, "confidence", 0.0),
            "central_bank_status": central_bank.status, "central_bank_effect": getattr(central_bank, "aggregate_gold_effect", "NEUTRAL"), "central_bank_score": getattr(central_bank, "aggregate_score", 0.0), "central_bank_confidence": getattr(central_bank, "confidence", 0.0),
            "cot_status": cot_intelligence.status, "cot_effect": getattr(cot_intelligence, "aggregate_gold_effect", "NEUTRAL"), "cot_score": getattr(cot_intelligence, "aggregate_score", 0.0), "cot_confidence": getattr(cot_intelligence, "confidence", 0.0),
            "open_interest_status": open_interest_intelligence.status, "open_interest_effect": getattr(open_interest_intelligence, "aggregate_gold_effect", "NEUTRAL"), "open_interest_score": getattr(open_interest_intelligence, "aggregate_score", 0.0), "open_interest_confidence": getattr(open_interest_intelligence, "confidence", 0.0),
            "etf_flow_status": etf_flow_intelligence.status, "etf_flow_effect": getattr(etf_flow_intelligence, "aggregate_gold_effect", "NEUTRAL"), "etf_flow_score": getattr(etf_flow_intelligence, "aggregate_score", 0.0), "etf_flow_confidence": getattr(etf_flow_intelligence, "confidence", 0.0),
            "usd_index_status": usd_index_intelligence.status, "usd_index_effect": getattr(usd_index_intelligence, "aggregate_gold_effect", "NEUTRAL"), "usd_index_score": getattr(usd_index_intelligence, "aggregate_score", 0.0), "usd_index_confidence": getattr(usd_index_intelligence, "confidence", 0.0),
            "bond_yield_status": bond_yield_intelligence.status, "bond_yield_effect": bond_yield_intelligence.aggregate_gold_effect, "bond_yield_score": bond_yield_intelligence.aggregate_score, "bond_yield_confidence": getattr(bond_yield_intelligence, "confidence", 0.0),
        })
        decision_intelligence = DecisionIntelligenceFoundationRuntime().evaluate_one({
            **dict(record), "mode": mode,
            "market_regime_status": market_regime_v2.status,
            "market_regime_direction": market_regime_v2.directional_bias,
            "market_regime_confidence": market_regime_v2.confidence,
            "market_regime": market_regime_v2.regime,
            "market_regime_bias": market_regime_v2.directional_bias,
            "market_structure_status": _upper(record.get("market_structure_status"), "WAITING"),
            "market_structure_direction": _upper(record.get("market_structure_direction"), "WAIT"),
            "market_structure_confidence": float(record.get("market_structure_confidence", 0.0) or 0.0),
            "multi_timeframe_status": _upper(record.get("multi_timeframe_status"), "WAITING"),
            "multi_timeframe_direction": _upper(record.get("multi_timeframe_direction"), "WAIT"),
            "multi_timeframe_confidence": float(record.get("multi_timeframe_confidence", 0.0) or 0.0),
            "liquidity_status": _upper(record.get("liquidity_status"), "WAITING"),
            "liquidity_direction": _upper(record.get("liquidity_direction"), "WAIT"),
            "liquidity_confidence": float(record.get("liquidity_confidence", 0.0) or 0.0),
            "trading_cost_status": "READY" if bool(record.get("trading_cost_allowed", True)) else "BLOCKED",
            "trading_cost_direction": "WAIT",
            "trading_cost_confidence": 1.0,
            "risk_status": "READY" if bool(record.get("risk_allowed", True)) else "BLOCKED",
            "risk_direction": "WAIT",
            "risk_confidence": 1.0,
        })
        consensus_engine = ConsensusEngineRuntime().evaluate_one({
            **dict(record),
            "market_regime_status": market_regime_v2.status,
            "market_regime_direction": market_regime_v2.directional_bias,
            "market_regime_confidence": market_regime_v2.confidence,
        })
        conflict_resolver = ConflictResolverRuntime().evaluate_one(record)
        opportunity_ranking = OpportunityRankingRuntime().evaluate_one({
            **dict(record),
            "resolved_consensus": conflict_resolver.resolved_consensus,
            "market_regime_confidence": market_regime_v2.confidence,
            "consensus_confidence": consensus_engine.agreement_ratio,
        })
        trade_scoring = TradeScoringRuntime().evaluate_one({**dict(record), "ranked_opportunities": [item.__dict__ for item in opportunity_ranking.ranked_opportunities]})
        unit_allocation = UnitAllocationRuntime().evaluate_one({**dict(record), "trade_scores": [item.__dict__ for item in trade_scoring.scores]})
        entry_validation = EntryValidationRuntime().evaluate_one({
            **dict(record),
            "market_regime_status": market_regime_v2.status,
            "market_regime_ready": market_regime_v2.status == "READY",
            "conflict_level": getattr(conflict_resolver, "conflict_level", record.get("conflict_level", "LOW")),
            "unit_allocations": [item.__dict__ for item in unit_allocation.allocations],
        })
        exit_validation = ExitValidationRuntime().evaluate_one({**dict(record), "market_regime_ready": market_regime_v2.status == "READY"})
        portfolio_decision = PortfolioDecisionRuntime().evaluate_one({
            **dict(record),
            "entry_validation": entry_validation.__dict__,
            "exit_validation": exit_validation.__dict__,
            "current_units": getattr(paper, "current_units", record.get("current_units", 0)),
            "maximum_units": record.get("maximum_units", record.get("profile_max_units", 1)),
        })
        decision_certification = DecisionIntelligenceCertificationRuntime().evaluate_one({
            **dict(record),
            "market_regime_status": market_regime_v2.status,
            "decision_intelligence_status": decision_intelligence.status,
            "consensus_status": consensus_engine.status,
            "conflict_resolver_status": conflict_resolver.status,
            "opportunity_ranking_status": opportunity_ranking.status,
            "trade_scoring_status": trade_scoring.status,
            "unit_allocation_status": unit_allocation.status,
            "entry_validation_status": entry_validation.status,
            "exit_validation_status": exit_validation.status,
            "portfolio_decision_status": portfolio_decision.status,
            "direct_execution": portfolio_decision.direct_execution,
            "lot_per_unit": 0.01,
        })
        execution_intelligence = ExecutionIntelligenceFoundationRuntime().evaluate_one({
            **dict(record),
            "decision_certification_status": decision_certification.status,
            "portfolio_decision_status": portfolio_decision.status,
            "portfolio_decision": portfolio_decision.portfolio_decision,
            "entry_validation_status": entry_validation.status,
            "conflict_level": getattr(conflict_resolver, "conflict_level", "LOW"),
            "approved_units": portfolio_decision.approved_units,
            "risk_allowed": getattr(portfolio_decision, "portfolio_risk_status", "READY") not in {"BLOCKED", "HIGH"},
            "timing_allowed": market_calendar.trading_allowed,
            "trading_cost_allowed": bool(record.get("trading_cost_allowed", True)),
            "market_open": market_calendar.market_open,
            "calendar_allowed": economic_calendar.trading_allowed,
            "decision_confidence": getattr(decision_intelligence, "confidence", 0.0),
            "direct_execution": False,
            "live_execution_enabled": False,
            "lot_per_unit": 0.01,
        })
        smart_entry = SmartEntryRuntime().evaluate_one({
            **dict(record),
            "execution_readiness": execution_intelligence.execution_readiness,
            "portfolio_decision": portfolio_decision.portfolio_decision,
            "approved_units": portfolio_decision.approved_units,
            "direction": record.get("direction", getattr(portfolio_decision, "portfolio_direction", record.get("entry_direction", "WAIT"))),
            "lot_per_unit": 0.01,
            "direct_execution": False,
            "live_execution_enabled": False,
        })
        smart_exit = SmartExitRuntime().evaluate_one({
            **dict(record),
            "portfolio_decision": portfolio_decision.portfolio_decision,
            "current_units": record.get("current_units", record.get("position_units", 0)),
            "risk_allowed": getattr(portfolio_decision, "portfolio_risk_status", "READY") not in {"BLOCKED", "HIGH"},
            "timing_allowed": market_calendar.trading_allowed,
            "trading_cost_allowed": bool(record.get("trading_cost_allowed", True)),
            "lot_per_unit": 0.01,
            "direct_execution": False,
            "live_execution_enabled": False,
        })
        dynamic_stop_loss = DynamicStopLossRuntime().evaluate_one({
            **dict(record),
            "current_units": record.get("current_units", record.get("position_units", 0)),
            "risk_allowed": getattr(portfolio_decision, "portfolio_risk_status", "READY") not in {"BLOCKED", "HIGH"},
            "timing_allowed": market_calendar.trading_allowed,
            "lot_per_unit": 0.01,
            "direct_execution": False,
            "live_execution_enabled": False,
        })
        dynamic_take_profit = DynamicTakeProfitRuntime().evaluate_one({
            **dict(record),
            "current_units": record.get("current_units", record.get("position_units", 1)),
            "risk_allowed": getattr(portfolio_decision, "portfolio_risk_status", "READY") not in {"BLOCKED", "HIGH"},
            "timing_allowed": market_calendar.trading_allowed,
            "lot_per_unit": 0.01,
            "direct_execution": False,
            "live_execution_enabled": False,
        })
        validation_items: list[str] = []
        if broker != VERSION1_BROKER:
            validation_items.append("version1_xm_only_required")
        if symbol != VERSION1_SYMBOL:
            validation_items.append("version1_gold_only_required")
        if mode == "LIVE" or bool(record.get("live_execution_enabled", False)):
            validation_items.append("live_execution_blocked_for_dashboard_ui")
        if mode not in _ALLOWED_MODES:
            validation_items.append("dashboard_ui_allows_simulation_or_paper_only")
        if validation_items:
            status, reason, ready = "BLOCKED", "dashboard_ui_blocked_by_version1_or_live_policy", False
        elif runtime.status == "BLOCKED" or foundation.status == "BLOCKED":
            status, reason, ready = "BLOCKED", "dashboard_ui_blocked_by_runtime_dependency", False
        elif runtime.status in {"WAITING", "REVIEW", "RECOVERING"} or foundation.status == "REVIEW":
            status, reason, ready = "WAITING", "dashboard_ui_waiting_for_runtime_dependency", True
        else:
            status, reason, ready = "READY", "dashboard_ui_visible_launcher_ready", True
        panels = (
            _runtime_panel(runtime),
            _integrated_intelligence_panel(integrated),
            _intelligence_panel(record),
            _trading_panel(paper),
            _analytics_panel(research),
            _bank_panel(afip_bank),
            _research_panel(research),
            _system_panel(record, runtime, vps_health, mt5_account, internet),
            _mt5_account_panel(mt5_account),
            _internet_panel(internet),
            _market_calendar_panel(market_calendar),
            _historical_data_panel(historical_data),
            _dashboard_live_runtime_panel(dashboard_live),
            _runtime_supervisor_panel(runtime_supervisor),
            _production_certification_panel(production_certification),
            _profile_customization_panel(profile_customization),
            _economic_calendar_intelligence_panel(economic_calendar),
            _news_intelligence_panel(news_intelligence),
            _gold_macro_intelligence_panel(gold_macro),
            _central_bank_intelligence_panel(central_bank),
            _cot_intelligence_panel(cot_intelligence),
            _open_interest_intelligence_panel(open_interest_intelligence),
            _etf_flow_intelligence_panel(etf_flow_intelligence),
            _usd_index_intelligence_panel(usd_index_intelligence),
            _bond_yield_intelligence_panel(bond_yield_intelligence),
            _market_regime_v2_panel(market_regime_v2),
            _decision_intelligence_foundation_panel(decision_intelligence),
            _consensus_engine_panel(consensus_engine),
            _conflict_resolver_panel(conflict_resolver),
            _opportunity_ranking_panel(opportunity_ranking),
            _trade_scoring_panel(trade_scoring),
            _unit_allocation_panel(unit_allocation),
            _entry_validation_panel(entry_validation),
            _exit_validation_panel(exit_validation),
            _portfolio_decision_panel(portfolio_decision),
            _decision_intelligence_certification_panel(decision_certification),
            _execution_intelligence_foundation_panel(execution_intelligence),
            _smart_entry_panel(smart_entry),
            _smart_exit_panel(smart_exit),
            _dynamic_stop_loss_panel(dynamic_stop_loss),
            _dynamic_take_profit_panel(dynamic_take_profit),
            _market_panel(record, market_calendar),
            _order_center_panel(paper),
            _explainable_order_center_panel(explainable_orders),
        )
        if production is not None:
            panels = panels + (_production_readiness_panel(production),)
        if validation_items:
            panels = (_policy_panel(validation_items),) + panels
        return DashboardUIReport(
            status=status,
            reason=reason,
            page_title="AFIP Dashboard — Milestone H Pack 10" if production is not None else "AFIP Dashboard — Milestone H Pack 9",
            profile_name=profile_name,
            broker=broker,
            symbol=symbol,
            mode=mode,
            live_execution_enabled=False,
            panels=panels,
            navigation_sections=("Runtime", "Intelligence", "Trading", "Analytics", "AFIP Bank", "Research", "System", "Market", "Order Center") + (("Production Readiness",) if production is not None else ()),
            visible_dashboard_ready=ready,
        )

    def explain_one(self, record: Mapping[str, Any]) -> DashboardUIReport:
        return self.evaluate_one(record)

    def render_html(self, record: Mapping[str, Any]) -> str:
        report = self.evaluate_one(record)
        cards = "\n".join(_panel_html(panel) for panel in report.panels)
        nav = "".join(f"<li>{escape(section)}</li>" for section in report.navigation_sections)
        return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>{escape(report.page_title)}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f7f7; color: #222; }}
header, section {{ background: white; border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin-bottom: 14px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }}
.status {{ font-weight: bold; }}
table {{ width: 100%; border-collapse: collapse; }}
td {{ border-top: 1px solid #eee; padding: 6px 4px; vertical-align: top; }}
td:first-child {{ font-weight: bold; width: 42%; }}
small {{ color: #555; }}
</style>
</head>
<body>
<header>
<h1>{escape(report.page_title)}</h1>
<p class=\"status\">Status: {escape(report.status)} — {escape(report.reason)}</p>
<p>Profile: {escape(report.profile_name)} | Broker: {escape(report.broker)} | Symbol: {escape(report.symbol)} | Mode: {escape(report.mode)} | Live Execution: {escape(str(report.live_execution_enabled))}</p>
<small>Presentation layer only. No trading logic changed. Live trading remains disabled.</small>
<nav><ul>{nav}</ul></nav>
</header>
<div class=\"grid\">
{cards}
</div>
</body>
</html>
"""

    def write_html(self, record: Mapping[str, Any], output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_html(record), encoding="utf-8")
        return path


def _policy_panel(validation_items: list[str]) -> DashboardPanel:
    return DashboardPanel("policy", "Production Policy", "นโยบายการใช้งาน", "BLOCKED", "Dashboard blocks unsafe or unsupported runtime modes.", "Dashboard บล็อกโหมดที่ไม่ปลอดภัยหรือไม่อยู่ใน Version 1", tuple((item, "BLOCKED") for item in validation_items))


def _runtime_panel(runtime: Any) -> DashboardPanel:
    return DashboardPanel("runtime", "Dashboard Runtime", "สถานะระบบ", runtime.status, "Shows runtime, dependency, and waiting status.", "แสดงสถานะ Runtime และเหตุผลที่รอ", (
        ("Runtime Gate", runtime.dashboard_runtime_gate),
        ("Reason", runtime.reason),
        ("Profile", runtime.profile_status),
        ("Connection", runtime.connection_status),
        ("Historical Data", runtime.historical_data_status),
        ("Runtime Service", runtime.runtime_service_status),
    ))



def _integrated_intelligence_panel(integrated: Any) -> DashboardPanel:
    rows: list[tuple[str, str]] = [
        ("Integration Status", integrated.status),
        ("Reason", integrated.reason),
        ("Research Statistics", integrated.research_statistics_scope),
        ("Live Statistics", integrated.live_statistics_scope),
        ("Decision Waiting", integrated.decision_explanation.waiting_reason),
        ("Decision Holding", integrated.decision_explanation.holding_reason),
        ("Expected Next Action", integrated.decision_explanation.expected_next_action),
        ("Risk Status", integrated.decision_explanation.risk_status),
    ]
    for row in integrated.engine_rows:
        rows.append((f"{row.status_icon} {row.english_name}", f"{row.status} | {row.thai_name} | confidence={row.confidence} | waiting={row.waiting_reason}"))
    return DashboardPanel(
        "dashboard_intelligence",
        "Dashboard Intelligence Integration",
        "การรวมข้อมูลอัจฉริยะของแดชบอร์ด",
        integrated.status,
        "Combines existing runtime, profile, research, paper trading, AFIP Bank, market, and order explainability into one observable dashboard data model.",
        "รวมข้อมูล Runtime, Profile, Research, Paper Trading, AFIP Bank, Market และเหตุผลของคำสั่งไว้ในโมเดลแดชบอร์ดเดียว",
        tuple(rows),
    )

def _intelligence_panel(record: Mapping[str, Any]) -> DashboardPanel:
    rows = (
        ("Market Regime", _text(record.get("market_regime", "TRENDING"), "TRENDING")),
        ("Input", _text(record.get("intelligence_input", "MT5 OHLC multi-timeframe data"), "MT5 OHLC multi-timeframe data")),
        ("Output", _text(record.get("intelligence_output", "paper_trading_decision_context"), "paper_trading_decision_context")),
        ("Confidence", _text(record.get("confidence", 0), "0")),
        ("Waiting Reason", _text(record.get("waiting_reason", "waiting_for_complete_runtime_review"), "waiting_for_complete_runtime_review")),
        ("Health", _text(record.get("intelligence_health", "READY"), "READY")),
    )
    return DashboardPanel("intelligence", "Dashboard Intelligence", "ปัญญาระบบ", "READY", "Displays engine input, output, confidence, and health.", "แสดงข้อมูลเข้า ผลลัพธ์ ความมั่นใจ และสุขภาพของ Engine", rows)


def _trading_panel(paper: Any) -> DashboardPanel:
    return DashboardPanel("trading", "Dashboard Trading", "การเทรดจำลอง", paper.status, "Displays paper trading state without broker execution.", "แสดงสถานะ Paper Trading โดยไม่ส่งคำสั่งจริง", (
        ("Order Count", str(paper.order_count)),
        ("Waiting", str(paper.waiting_count)),
        ("Ready", str(paper.ready_count)),
        ("Opened", str(paper.opened_count)),
        ("Managing", str(paper.managing_count)),
        ("Closed", str(paper.closed_count)),
        ("Current Units", str(paper.current_units)),
    ))


def _analytics_panel(research: Any) -> DashboardPanel:
    return DashboardPanel("analytics", "Dashboard Analytics", "สถิติและการวิเคราะห์", research.status, "Separates research and live statistics.", "แยกสถิติ Research และ Live ออกจากกัน", (
        ("Research Scope", research.research_scope),
        ("Live Scope", research.live_scope),
        ("Completed Research Orders", str(research.completed_research_orders)),
        ("Standard Learning", str(research.standard_learning_candidate)),
        ("Policy", research.standard_learning_policy),
    ))


def _bank_panel(bank: Any) -> DashboardPanel:
    return DashboardPanel("afip_bank", "AFIP Bank Live", "ธนาคาร AFIP แบบสด", bank.status, bank.dashboard_explanation_en, bank.dashboard_explanation_th, (
        ("Currency", bank.currency),
        ("Initial Capital", str(bank.initial_capital)),
        ("Deposits", str(bank.deposits)),
        ("Withdrawals", str(bank.withdrawals)),
        ("Balance", str(bank.balance)),
        ("Equity", str(bank.equity)),
        ("Reserve", str(bank.reserve)),
        ("Allocation", str(bank.available_allocation)),
        ("ROI", f"{bank.lifetime_return_percent}%"),
        ("Floating Profit", str(bank.floating_profit)),
        ("Closed Profit", str(bank.closed_profit)),
        ("Transactions", str(bank.transaction_count)),
        ("Reason", bank.reason),
        ("คำอธิบายภาษาไทย", bank.dashboard_explanation_th),
        ("เงินฝาก", str(bank.deposits)),
        ("เงินถอน", str(bank.withdrawals)),
        ("เงินที่จัดสรรได้", str(bank.available_allocation)),
    ))


def _research_panel(research: Any) -> DashboardPanel:
    groups = ("Top 10 Trading Hours", "Top 10 Trading Sessions", "Top 10 Market Regimes", "Top 10 Entry Plans", "Top 10 Exit Plans", "Top 10 Patterns", "Top 10 Engine Combinations", "Top 10 Profit Reasons", "Top 10 Loss Reasons")
    return DashboardPanel("research", "Research Center", "ศูนย์วิจัย", research.status, "Displays required research groups.", "แสดงกลุ่มสถิติวิจัยที่จำเป็น", tuple((group, "available") for group in groups))


def _system_panel(record: Mapping[str, Any], runtime: Any, vps_health: Any, mt5_account: Any, internet: Any) -> DashboardPanel:
    status = "READY" if runtime.status in {"READY", "WAITING"} and vps_health.status in {"READY", "REVIEW"} else runtime.status
    return DashboardPanel("system", "Dashboard System", "ระบบ", status, "Displays live VPS health and connectivity status.", "แสดงสุขภาพ VPS สดและสถานะการเชื่อมต่อ", (
        ("Internet Status", internet.internet_status),
        ("Internet Gate", internet.connection_gate),
        ("Internet Latency", f"{internet.dns_latency_ms} ms"),
        ("Disconnect Count", str(internet.disconnect_count)),
        ("Reconnect Count", str(internet.reconnect_count)),
        ("Disconnect Duration", f"{internet.disconnect_duration_seconds} sec"),
        ("MT5 Status", runtime.connection_status),
        ("Broker Status", internet.broker_status if internet.broker_status in {"READY", "REVIEW", "ONLINE", "CONNECTED"} else mt5_account.status),
        ("Broker Latency", f"{internet.broker_latency_ms} ms"),
        ("MT5 Account", mt5_account.status),
        ("MT5 Server", mt5_account.server),
        ("MT5 Equity", str(mt5_account.equity)),
        ("MT5 Spread", f"{mt5_account.spread_points} pts"),
        ("VPS Health", vps_health.status),
        ("VPS Reason", vps_health.reason),
        ("Hostname", vps_health.hostname),
        ("Windows", vps_health.windows_version),
        ("Python", vps_health.python_version),
        ("Uptime Seconds", str(vps_health.uptime_seconds)),
        ("CPU", f"{vps_health.cpu_percent}%"),
        ("RAM", f"{vps_health.ram_percent}%"),
        ("Disk", f"{vps_health.disk_percent}% used / {vps_health.disk_free_gb} GB free"),
    ))


def _mt5_account_panel(mt5_account: Any) -> DashboardPanel:
    return DashboardPanel(
        "mt5_account",
        "MT5 Live Account",
        "บัญชี MT5 สด",
        mt5_account.status,
        "Displays read-only MT5 account, broker, balance, equity, margin, and tick data without enabling live execution.",
        "แสดงบัญชี MT5, Broker, Balance, Equity, Margin และ Tick แบบอ่านอย่างเดียวโดยไม่เปิดเงินจริง",
        (
            ("Reason", mt5_account.reason),
            ("Broker", mt5_account.broker),
            ("Server", mt5_account.server),
            ("Login", mt5_account.login),
            ("Account Name", mt5_account.account_name),
            ("Currency", mt5_account.currency),
            ("Balance", str(mt5_account.balance)),
            ("Equity", str(mt5_account.equity)),
            ("Margin", str(mt5_account.margin)),
            ("Free Margin", str(mt5_account.free_margin)),
            ("Leverage", mt5_account.leverage),
            ("Symbol", mt5_account.symbol),
            ("Bid", str(mt5_account.bid)),
            ("Ask", str(mt5_account.ask)),
            ("Spread", f"{mt5_account.spread_points} pts"),
            ("Last Tick", mt5_account.last_tick_time),
            ("Gate", mt5_account.account_gate),
        ),
    )


def _internet_panel(internet: Any) -> DashboardPanel:
    return DashboardPanel(
        "internet_monitor",
        "Internet Monitor",
        "ตัวตรวจสอบอินเทอร์เน็ต",
        internet.status,
        "Displays internet, DNS, broker reachability, latency, disconnect count, and reconnect count without enabling live execution.",
        "แสดงอินเทอร์เน็ต DNS การเชื่อมต่อโบรกเกอร์ ความหน่วง จำนวนครั้งที่หลุด และจำนวนครั้งที่เชื่อมต่อใหม่ โดยไม่เปิดเงินจริง",
        (
            ("Reason", internet.reason),
            ("Internet Status", internet.internet_status),
            ("DNS Status", internet.dns_status),
            ("DNS Latency", f"{internet.dns_latency_ms} ms"),
            ("Broker Status", internet.broker_status),
            ("Broker Host", internet.broker_host),
            ("Broker Port", str(internet.broker_port)),
            ("Broker Latency", f"{internet.broker_latency_ms} ms"),
            ("Disconnect Count", str(internet.disconnect_count)),
            ("Reconnect Count", str(internet.reconnect_count)),
            ("Disconnect Duration", f"{internet.disconnect_duration_seconds} sec"),
            ("Gate", internet.connection_gate),
        ),
    )


def _market_calendar_panel(calendar: Any) -> DashboardPanel:
    return DashboardPanel(
        "market_calendar",
        "Market Session & Trading Calendar",
        "ปฏิทินตลาดและช่วงเวลาเทรด",
        calendar.status,
        "Explains market open, market close, weekend, holiday, session, trading permission, and block reason without enabling live execution.",
        "อธิบายตลาดเปิด ปิด เสาร์อาทิตย์ วันหยุด ช่วงเวลาเทรด การอนุญาตเทรด และเหตุผลที่บล็อก โดยไม่เปิดเงินจริง",
        (
            ("Current Time UTC", calendar.current_time_utc),
            ("Market Open", str(calendar.market_open)),
            ("Market Closed", str(calendar.market_closed)),
            ("Weekend", str(calendar.weekend)),
            ("Holiday", str(calendar.holiday)),
            ("Holiday Name", calendar.holiday_name),
            ("Asia Session", str(calendar.asia_session)),
            ("London Session", str(calendar.london_session)),
            ("New York Session", str(calendar.new_york_session)),
            ("Active Sessions", ", ".join(calendar.active_sessions) if calendar.active_sessions else "none"),
            ("Primary Session", calendar.primary_session),
            ("Trading Allowed", str(calendar.trading_allowed)),
            ("Trading Block Reason", calendar.trading_block_reason),
            ("Dashboard Live Market Status", calendar.dashboard_market_status),
            ("Next Review Time", calendar.next_review_time_utc),
            ("Gate", calendar.calendar_gate),
        ),
    )



def _historical_data_panel(report: Any) -> DashboardPanel:
    rows = [("Source", report.source), ("Total Bars", str(report.total_bars)), ("Missing Bars", str(report.missing_bars)), ("Duplicate Bars", str(report.duplicate_bars)), ("Quality Score", str(report.quality_score)), ("Storage", report.storage_status), ("Research Ready", str(report.research_ready)), ("Walk Forward Ready", str(report.walk_forward_ready)), ("Next Action EN", report.next_action_en), ("Next Action TH", report.next_action_th)]
    rows.extend((f"{tf} Bars", str(count)) for tf, count in report.timeframe_bars)
    return DashboardPanel("historical_data", "Historical Data Manager", "ตัวจัดการข้อมูลย้อนหลัง", report.status, "Shows read-only historical coverage, quality, readiness, and next action.", "แสดงความครอบคลุม คุณภาพ ความพร้อม และขั้นตอนถัดไปของข้อมูลย้อนหลังแบบอ่านอย่างเดียว", tuple(rows))


def _dashboard_live_runtime_panel(report: Any) -> DashboardPanel:
    return DashboardPanel(
        "dashboard_live_runtime",
        "Dashboard Live Runtime",
        "ระบบ Dashboard แบบสด",
        report.status,
        "Shows refresh state, snapshot freshness, dependency readiness, waiting reason, and expected next action without enabling live execution.",
        "แสดงสถานะการรีเฟรช ความสดของ Snapshot ความพร้อมของส่วนประกอบ เหตุผลที่รอ และการกระทำถัดไป โดยไม่เปิดเงินจริง",
        (
            ("Reason", report.reason),
            ("Runtime State", report.runtime_state),
            ("Data State", report.data_state),
            ("Refresh Interval", f"{report.refresh_interval_seconds} sec"),
            ("Last Refresh UTC", report.last_refresh_utc),
            ("Next Refresh UTC", report.next_refresh_utc),
            ("Snapshot Sequence", str(report.snapshot_sequence)),
            ("Data Age", f"{report.data_age_seconds} sec"),
            ("Stale After", f"{report.stale_after_seconds} sec"),
            ("Data Fresh", str(report.data_fresh)),
            ("Dependency Ready", str(report.dependency_ready)),
            ("Dashboard Live Ready", str(report.dashboard_live_ready)),
            ("Waiting Reason EN", report.waiting_reason_en),
            ("Waiting Reason TH", report.waiting_reason_th),
            ("Expected Next Action EN", report.expected_next_action_en),
            ("Expected Next Action TH", report.expected_next_action_th),
            ("Live Execution", str(report.live_execution_enabled)),
        ),
    )


def _runtime_supervisor_panel(supervisor: Any) -> DashboardPanel:
    return DashboardPanel(
        "runtime_supervisor",
        "Runtime Supervisor",
        "ระบบกำกับ Runtime",
        supervisor.status,
        "Aggregates health, warnings, critical dependencies, recovery guidance, confidence, and the next review time.",
        "รวมสุขภาพระบบ คำเตือน ส่วนประกอบวิกฤต แนวทางกู้คืน ความมั่นใจ และเวลาตรวจครั้งถัดไป",
        (
            ("Runtime Health", supervisor.runtime_health),
            ("Healthy Modules", str(supervisor.healthy_modules)),
            ("Warning Modules", str(supervisor.warning_modules)),
            ("Critical Modules", str(supervisor.critical_modules)),
            ("Recovery Action EN", supervisor.recovery_action_en),
            ("Recovery Action TH", supervisor.recovery_action_th),
            ("Expected Next Check EN", supervisor.expected_next_check_en),
            ("Expected Next Check TH", supervisor.expected_next_check_th),
            ("Supervisor Confidence", str(supervisor.supervisor_confidence)),
            ("Live Execution", str(supervisor.live_execution_enabled)),
        ),
    )


def _production_certification_panel(report: Any) -> DashboardPanel:
    return DashboardPanel(
        "production_certification",
        "Production Certification",
        "การรับรอง Production",
        report.status,
        report.certification_summary_en,
        report.certification_summary_th,
        (
            ("Certification Level", report.certification_level),
            ("Passed Checks", str(report.passed_checks)),
            ("Total Checks", str(report.total_checks)),
            ("Failed Checks", ", ".join(report.failed_checks) if report.failed_checks else "NONE"),
            ("Market Intelligence Ready", str(report.market_intelligence_ready)),
            ("Next Action EN", report.next_action_en),
            ("Next Action TH", report.next_action_th),
            ("Execution", report.execution_status),
            ("Live Execution", str(report.live_execution_enabled)),
        ),
    )


def _exit_validation_panel(report: Any) -> DashboardPanel:
    rows = [
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Selected Position / สถานะที่เลือก", report.selected_position_id),
        ("Approved Action / การดำเนินการที่อนุมัติ", report.approved_action),
        ("Approved Units / Unit ที่อนุมัติ", str(report.approved_units)),
        ("Holding Reason EN", report.holding_reason_en),
        ("Holding Reason TH", report.holding_reason_th),
        ("Stop Loss Move Reason EN", report.stop_loss_move_reason_en),
        ("Stop Loss Move Reason TH", report.stop_loss_move_reason_th),
        ("Take Profit Change Reason EN", report.take_profit_change_reason_en),
        ("Take Profit Change Reason TH", report.take_profit_change_reason_th),
        ("Trailing Stop Reason EN", report.trailing_stop_reason_en),
        ("Trailing Stop Reason TH", report.trailing_stop_reason_th),
        ("Partial Close Reason EN", report.partial_close_reason_en),
        ("Partial Close Reason TH", report.partial_close_reason_th),
        ("Exit Reason EN", report.exit_reason_en),
        ("Exit Reason TH", report.exit_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.direct_execution)),
    ]
    for item in report.validations[:10]:
        rows.append((f"{item.position_id} / {item.direction}", f"requested={item.recommended_action} | approved={item.approved_action} | action_approved={item.action_approved} | units={item.units} | hold={item.hold_allowed} | partial={item.partial_close_allowed} | sl_move={item.stop_loss_move_allowed} | tp_change={item.take_profit_change_allowed} | trailing={item.trailing_stop_allowed} | exit={item.full_exit_allowed} | blocks={','.join(item.block_reasons)} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("exit_validation", "Exit Validation Engine", "กลไกตรวจสอบการถือและออกจากสถานะ", report.status, "Validates holding, stop-loss moves, take-profit changes, trailing stops, partial closes, and exits without modifying positions.", "ตรวจสอบการถือ เลื่อน Stop Loss เปลี่ยน Take Profit Trailing Stop ปิดบางส่วน และออกจากสถานะโดยไม่แก้ไขสถานะจริง", tuple(rows))


def _portfolio_decision_panel(report: Any) -> DashboardPanel:
    rows = [
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Portfolio / พอร์ต", report.selected_portfolio_id),
        ("Decision / การตัดสินใจ", report.portfolio_decision),
        ("Direction / ทิศทาง", report.selected_direction),
        ("Approved Units / Unit ที่อนุมัติ", str(report.approved_units)),
        ("Current Units / Unit ปัจจุบัน", str(report.current_units)),
        ("Maximum Units / Unit สูงสุด", str(report.maximum_units)),
        ("Available Units / Unit ที่เหลือ", str(report.available_units)),
        ("Portfolio Risk / ความเสี่ยงพอร์ต", report.portfolio_risk_status),
        ("Waiting Reason EN", report.waiting_reason_en),
        ("Waiting Reason TH", report.waiting_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.direct_execution)),
    ]
    for item in report.decisions[:10]:
        rows.append((f"{item.portfolio_id} / {item.decision}", f"direction={item.direction} | approved={item.approved} | current={item.current_units} | max={item.maximum_units} | available={item.available_units} | entry={item.entry_units} | exit={item.exit_units} | risk={item.risk_allowed} | exposure={item.exposure_allowed} | blocks={','.join(item.block_reasons)} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("portfolio_decision", "Portfolio Decision Engine", "กลไกตัดสินใจระดับพอร์ต", report.status, "Combines entry, exit, risk, exposure, and fixed-unit capacity into one explainable portfolio decision without executing orders.", "รวมจุดเข้า การออก ความเสี่ยง Exposure และความจุ Unit คงที่เป็นการตัดสินใจระดับพอร์ตที่อธิบายได้โดยไม่ส่งคำสั่งซื้อขาย", tuple(rows))

def _decision_intelligence_certification_panel(report: Any) -> DashboardPanel:
    rows = (
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Certification Level / ระดับการรับรอง", report.certification_level),
        ("Passed Checks / รายการที่ผ่าน", f"{report.passed_checks}/{report.total_checks}"),
        ("Failed Checks / รายการที่ไม่ผ่าน", ", ".join(report.failed_checks) or "NONE"),
        ("Decision Intelligence Ready / พร้อมใช้งาน", str(report.decision_intelligence_ready)),
        ("Summary EN", report.certification_summary_en),
        ("Summary TH", report.certification_summary_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.direct_execution)),
        ("Live Execution / คำสั่งจริง", str(report.live_execution_enabled)),
        ("Execution Status / สถานะการส่งคำสั่ง", report.execution_status),
    )
    return DashboardPanel("decision_intelligence_certification", "Decision Intelligence Certification", "การรับรอง Decision Intelligence", report.status, "Certifies Milestone J as explainable, deterministic, and simulation-only before Execution Intelligence begins.", "รับรอง Milestone J ว่าอธิบายได้ กำหนดผลซ้ำได้ และจำกัดเฉพาะ simulation ก่อนเริ่ม Execution Intelligence", rows)


def _execution_intelligence_foundation_panel(report: Any) -> DashboardPanel:
    rows = (
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Execution Stage / ขั้นตอน", report.execution_stage),
        ("Readiness / ความพร้อม", report.execution_readiness),
        ("Approval Stage / การอนุมัติ", report.approval_stage),
        ("Pipeline Progress / ความคืบหน้า", f"{report.pipeline_progress_percent}%"),
        ("Confidence / ความมั่นใจ", str(report.execution_confidence)),
        ("Simulation Ready / พร้อมจำลอง", str(report.simulation_ready)),
        ("No Order Sent / ไม่มีคำสั่งถูกส่ง", str(report.no_order_sent)),
        ("Approved Units / Unit ที่อนุมัติ", str(report.unit_count)),
        ("Lot per Unit", str(report.lot_per_unit)),
        ("Block Reasons / เหตุผลที่บล็อก", ", ".join(report.block_reasons) or "NONE"),
        ("Waiting Reason EN", report.waiting_reason_en),
        ("Waiting Reason TH", report.waiting_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Execution Status / สถานะการส่งคำสั่ง", report.execution_status),
        ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.direct_execution)),
        ("Live Execution / คำสั่งจริง", str(report.live_execution_enabled)),
    )
    return DashboardPanel("execution_intelligence_foundation", "Execution Intelligence Foundation", "รากฐานปัญญาการส่งคำสั่ง", report.status, "Converts certified portfolio decisions into an explainable simulation-only execution context. It never sends an order.", "แปลงการตัดสินใจระดับพอร์ตที่ผ่านการรับรองเป็นบริบทการส่งคำสั่งแบบ Simulation ที่อธิบายได้ และไม่ส่งคำสั่งจริง", rows)

def _smart_entry_panel(report: Any) -> DashboardPanel:
    rows = (
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Entry Plan / แผนจุดเข้า", report.entry_plan_status),
        ("Side / ฝั่ง", report.order_side),
        ("Order Type / ประเภทคำสั่ง", report.order_type),
        ("Reference Price / ราคาอ้างอิง", str(report.reference_price)),
        ("Stop Loss / จุดหยุดขาดทุน", str(report.stop_loss_price)),
        ("Take Profit / จุดทำกำไร", str(report.take_profit_price)),
        ("Reward/Risk", str(report.reward_risk_ratio)),
        ("Units / จำนวน Unit", str(report.unit_count)),
        ("Total Lot / Lot รวม", str(report.total_lot)),
        ("Simulation Instruction Ready / พร้อมจำลอง", str(report.simulation_instruction_ready)),
        ("No Order Sent / ไม่มีคำสั่งถูกส่ง", str(report.no_order_sent)),
        ("Block Reasons / เหตุผลที่บล็อก", ", ".join(report.block_reasons) or "NONE"),
        ("Entry Reason EN", report.entry_reason_en),
        ("Entry Reason TH", report.entry_reason_th),
        ("Waiting Reason EN", report.waiting_reason_en),
        ("Waiting Reason TH", report.waiting_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Execution Status / สถานะการส่งคำสั่ง", report.execution_status),
    )
    return DashboardPanel("smart_entry", "Smart Entry Engine", "กลไกวางแผนจุดเข้าอัจฉริยะ", report.status, "Builds a protected paper/demo entry instruction without sending a live order.", "สร้างคำสั่งจำลองสำหรับจุดเข้าที่มีการป้องกันความเสี่ยง โดยไม่ส่งคำสั่งจริง", rows)

def _smart_exit_panel(report: Any) -> DashboardPanel:
    rows = (
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Exit Plan / แผนออก", report.exit_plan_status),
        ("Action / การดำเนินการ", report.action),
        ("Current Units / Unit ปัจจุบัน", str(report.current_units)),
        ("Close Units / Unit ที่ปิด", str(report.close_units)),
        ("Remaining Units / Unit คงเหลือ", str(report.remaining_units)),
        ("Reference Price / ราคาอ้างอิง", str(report.reference_price)),
        ("Unrealized PnL / กำไรขาดทุนลอยตัว", str(report.unrealized_pnl)),
        ("Simulation Instruction Ready / พร้อมจำลอง", str(report.simulation_instruction_ready)),
        ("No Order Sent / ไม่มีคำสั่งถูกส่ง", str(report.no_order_sent)),
        ("Block Reasons / เหตุผลที่บล็อก", ", ".join(report.block_reasons) or "NONE"),
        ("Holding Reason EN", report.holding_reason_en),
        ("Holding Reason TH", report.holding_reason_th),
        ("Partial Close Reason EN", report.partial_close_reason_en),
        ("Partial Close Reason TH", report.partial_close_reason_th),
        ("Exit Reason EN", report.exit_reason_en),
        ("Exit Reason TH", report.exit_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Execution Status / สถานะการส่งคำสั่ง", report.execution_status),
    )
    return DashboardPanel("smart_exit", "Smart Exit Engine", "กลไกวางแผนออกอัจฉริยะ", report.status, "Builds hold, partial-close, or full-exit instructions for paper/demo positions without changing a live position.", "สร้างคำสั่งถือต่อ ปิดบางส่วน หรือออกทั้งหมดสำหรับสถานะจำลอง โดยไม่แก้ไขสถานะจริง", rows)

def _dynamic_stop_loss_panel(report: Any) -> DashboardPanel:
    rows = (
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Action / การดำเนินการ", report.action),
        ("Current Stop Loss / Stop Loss ปัจจุบัน", str(report.current_stop_loss)),
        ("Proposed Stop Loss / Stop Loss ที่เสนอ", str(report.proposed_stop_loss)),
        ("Reference Price / ราคาอ้างอิง", str(report.reference_price)),
        ("Risk Distance Before / ระยะความเสี่ยงก่อน", str(report.risk_distance_before)),
        ("Risk Distance After / ระยะความเสี่ยงหลัง", str(report.risk_distance_after)),
        ("Risk Reduction / ความเสี่ยงที่ลดลง", str(report.risk_reduction)),
        ("Move Approved / อนุมัติการเลื่อน", str(report.move_approved)),
        ("Simulation Instruction Ready / พร้อมจำลอง", str(report.simulation_instruction_ready)),
        ("No Order Sent / ไม่มีคำสั่งถูกส่ง", str(report.no_order_sent)),
        ("Block Reasons / เหตุผลที่บล็อก", ", ".join(report.block_reasons) or "NONE"),
        ("Stop Loss Move Reason EN", report.stop_loss_move_reason_en),
        ("Stop Loss Move Reason TH", report.stop_loss_move_reason_th),
        ("Holding Reason EN", report.holding_reason_en),
        ("Holding Reason TH", report.holding_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Execution Status / สถานะการส่งคำสั่ง", report.execution_status),
    )
    return DashboardPanel("dynamic_stop_loss", "Dynamic Stop Loss Intelligence", "ระบบวิเคราะห์ Stop Loss แบบปรับตามสถานการณ์", report.status, "Reviews a risk-reducing stop-loss proposal for paper/demo simulation without modifying a live position.", "ทบทวนข้อเสนอการเลื่อน Stop Loss ที่ลดความเสี่ยงสำหรับการจำลอง โดยไม่แก้ไขสถานะจริง", rows)

def _dynamic_take_profit_panel(report: Any) -> DashboardPanel:
    rows = (
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Action / การดำเนินการ", report.action),
        ("Current TP / Take Profit ปัจจุบัน", str(report.current_take_profit)),
        ("Proposed TP / Take Profit ที่เสนอ", str(report.proposed_take_profit)),
        ("Reference Price / ราคาอ้างอิง", str(report.reference_price)),
        ("Reward/Risk Before / ก่อนปรับ", str(report.reward_risk_before)),
        ("Reward/Risk After / หลังปรับ", str(report.reward_risk_after)),
        ("Change Approved / อนุมัติการเปลี่ยน", str(report.change_approved)),
        ("Simulation Ready / พร้อมจำลอง", str(report.simulation_instruction_ready)),
        ("No Order Sent / ไม่มีคำสั่งถูกส่ง", str(report.no_order_sent)),
        ("Block Reasons / เหตุผลที่บล็อก", ", ".join(report.block_reasons) or "NONE"),
        ("Take Profit Change Reason EN", report.take_profit_change_reason_en),
        ("Take Profit Change Reason TH", report.take_profit_change_reason_th),
        ("Holding Reason EN", report.holding_reason_en),
        ("Holding Reason TH", report.holding_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
    )
    return DashboardPanel("dynamic_take_profit", "Dynamic Take Profit Intelligence", "ระบบวิเคราะห์ Take Profit แบบปรับตามสถานการณ์", report.status, "Reviews a take-profit proposal for paper/demo simulation while preserving reward/risk and never modifying a live position.", "ทบทวนข้อเสนอ Take Profit สำหรับการจำลองโดยรักษา Reward/Risk และไม่แก้ไขสถานะจริง", rows)


def _market_panel(record: Mapping[str, Any], calendar: Any) -> DashboardPanel:
    return DashboardPanel("market", "Dashboard Market", "ตลาด", calendar.status, "Displays live market session and open/close status.", "แสดงสถานะตลาดสดและช่วงเวลาเทรด", (
        ("Market Open / Close", calendar.dashboard_market_status),
        ("Trading Session", calendar.primary_session),
        ("Trading Allowed", str(calendar.trading_allowed)),
        ("Trading Block Reason", calendar.trading_block_reason),
        ("Next Review Time", calendar.next_review_time_utc),
        ("Symbol", _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)),
        ("Broker", _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)),
    ))


def _order_center_panel(paper: Any) -> DashboardPanel:
    rows: list[tuple[str, str]] = [("Close Reason", paper.reason), ("Order Quality", "paper_order_quality_visible")]
    for order in paper.orders[:5]:
        rows.append((f"{order.order_id} Status", order.status))
        rows.append((f"{order.order_id} Holding Reason", order.holding_reason))
        rows.append((f"{order.order_id} Expected Next Action", order.expected_next_action))
        rows.append((f"{order.order_id} Risk", order.risk_status))
    return DashboardPanel("order_center", "Order Center", "ศูนย์คำสั่ง", paper.status, "Explains waiting, holding, risk, and next action for each paper order.", "อธิบายเหตุผลของการรอ ถือ ความเสี่ยง และการกระทำถัดไปของคำสั่งจำลอง", tuple(rows))


def _explainable_order_center_panel(report: Any) -> DashboardPanel:
    rows: list[tuple[str, str]] = [
        ("Reason", report.reason),
        ("Live Execution", str(report.live_execution_enabled)),
        ("Order Count", str(report.order_count)),
        ("Visible Fields", ", ".join(report.visible_explanation_fields)),
    ]
    if not report.orders:
        rows.append(("Waiting Reason / เหตุผลที่รอ", "explainable_order_center_waiting_for_paper_orders"))
    for order in report.orders[:5]:
        prefix = f"{order.order_id} {order.status}"
        rows.append((f"{prefix} Units", f"{order.units} unit(s) / {order.total_lot:.2f} lot"))
        rows.append((f"{prefix} Confidence / ความมั่นใจ", str(order.confidence)))
        rows.append((f"{prefix} Risk / ความเสี่ยง", order.risk_status))
        rows.append((f"{prefix} Expected Next Action / การกระทำถัดไป", order.expected_next_action))
        rows.append((f"{prefix} Next Review Time / เวลาตรวจสอบครั้งถัดไป", order.next_review_time))
        for item in order.explanations:
            rows.append((f"{prefix} {item.title_en} / {item.title_th}", f"{item.value} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel(
        "explainable_order_center",
        "Explainable Order Center",
        "ศูนย์คำสั่งแบบอธิบายได้",
        report.status,
        "Displays bilingual order explanations for waiting, entry, holding, stop loss, take profit, trailing, partial close, exit, confidence, risk, and next review time.",
        "แสดงเหตุผลคำสั่งสองภาษา ครอบคลุมการรอ เข้าเทรด ถือสถานะ Stop Loss Take Profit Trailing ปิดบางส่วน ออกจากสถานะ ความมั่นใจ ความเสี่ยง และเวลาตรวจสอบถัดไป",
        tuple(rows),
    )


def _panel_html(panel: DashboardPanel) -> str:
    rows = "\n".join(f"<tr><td>{escape(key)}</td><td>{escape(value)}</td></tr>" for key, value in panel.rows)
    return f"""<section id=\"{escape(panel.panel_id)}\">
<h2>{escape(panel.title_en)} / {escape(panel.title_th)}</h2>
<p class=\"status\">{escape(panel.status)}</p>
<p>{escape(panel.description_en)}<br><small>{escape(panel.description_th)}</small></p>
<table>{rows}</table>
</section>"""


def _production_readiness_panel(production: Any) -> DashboardPanel:
    return DashboardPanel(
        "production_readiness",
        "Production Readiness",
        "ความพร้อมก่อนใช้งานจริง",
        production.status,
        "Shows VPS, historical data, walk forward, research, paper, and demo readiness while live trading remains disabled.",
        "แสดงความพร้อมของ VPS ข้อมูลย้อนหลัง Walk Forward Research Paper และ Demo โดยยังไม่เปิดเงินจริง",
        (
            ("Release Stage", production.release_stage),
            ("Reason", production.reason),
            ("VPS", str(production.vps_ready)),
            ("Historical Data", str(production.historical_data_ready)),
            ("Walk Forward", str(production.walk_forward_ready)),
            ("Research", str(production.research_ready)),
            ("Paper Trading", str(production.paper_trading_ready)),
            ("Demo Trading", str(production.demo_trading_ready)),
            ("Live Execution", str(production.live_execution_enabled)),
        ),
    )


def _profile_customization_panel(report: Any) -> DashboardPanel:
    p = report.profile
    return DashboardPanel(
        "profile_customization", "Profile Customization", "การปรับแต่งโปรไฟล์", report.status,
        "Create, rename, duplicate, activate, archive, and assign reusable profiles with deterministic validation and version history.",
        "สร้าง เปลี่ยนชื่อ คัดลอก เปิดใช้งาน เก็บถาวร และกำหนดบัญชีให้โปรไฟล์ พร้อมการตรวจสอบและประวัติเวอร์ชัน",
        (("Profile Name / ชื่อโปรไฟล์", p.profile_name), ("Profile ID", p.profile_id), ("Base Profile / โปรไฟล์ต้นแบบ", p.base_profile), ("Risk / ความเสี่ยง", p.risk_level), ("Maximum Units / จำนวน Unit สูงสุด", str(p.maximum_units)), ("Capital per Unit / เงินทุนต่อ Unit", str(p.capital_per_unit)), ("Active / ใช้งานอยู่", str(p.active)), ("Archived / เก็บถาวร", str(p.archived)), ("Assigned Account / บัญชีที่กำหนด", p.assigned_account_id or "-"), ("Validation / การตรวจสอบ", ", ".join(report.validation_items) or "PASS"), ("Next Action / ขั้นตอนถัดไป", report.expected_next_action_en + " / " + report.expected_next_action_th), ("Live Execution", str(report.live_execution_enabled))),
    )


def _economic_calendar_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("Event Count / จำนวนเหตุการณ์", str(report.event_count)), ("High Impact / ผลกระทบสูง", str(report.high_impact_count)), ("Gold Relevant / เกี่ยวข้องกับทอง", str(report.gold_relevant_count)), ("Trading Allowed / อนุญาตให้เทรด", str(report.trading_allowed)), ("Trading Block Reason / เหตุผลบล็อก", report.trading_block_reason), ("Next Event UTC / ข่าวถัดไป", report.next_event_time_utc), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for event in report.events[:5]:
        rows.append((f"{event.title} / {event.impact}", f"{event.event_window} | gold={event.gold_relevance} | {event.minutes_until_event}m | EN: {event.explanation_en} | TH: {event.explanation_th}"))
    return DashboardPanel("economic_calendar_intelligence", "Economic Calendar Intelligence", "ปัญญาปฏิทินเศรษฐกิจ", report.status, "Converts economic events into structured gold intelligence. Events never execute orders directly.", "แปลงเหตุการณ์เศรษฐกิจเป็นข้อมูลอัจฉริยะสำหรับทองคำ โดยข่าวไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _news_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("News Items / จำนวนข่าว", str(report.item_count)), ("Unique / ข่าวไม่ซ้ำ", str(report.unique_item_count)), ("Duplicates / ข่าวซ้ำ", str(report.duplicate_count)), ("High Reliability / ความน่าเชื่อถือสูง", str(report.high_reliability_count)), ("Gold Relevant / เกี่ยวข้องกับทอง", str(report.gold_relevant_count)), ("Aggregate Sentiment / อารมณ์รวม", f"{report.aggregate_sentiment} ({report.aggregate_sentiment_score})"), ("Intelligence Ready / พร้อมใช้งาน", str(report.intelligence_ready)), ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.execution_allowed)), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for item in report.items[:5]:
        rows.append((f"{item.source} / {item.category}", f"{item.sentiment} | reliability={item.reliability_score} | gold={item.gold_relevance} | duplicate={item.duplicate} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("news_intelligence", "News Intelligence", "ปัญญาข่าวสาร", report.status, "Transforms supplied news into structured intelligence with source reliability and duplicate control. News never executes orders directly.", "แปลงข่าวที่ได้รับเป็นข้อมูลอัจฉริยะ พร้อมประเมินความน่าเชื่อถือและควบคุมข่าวซ้ำ โดยข่าวไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _gold_macro_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("Indicators / ตัวชี้วัด", str(report.indicator_count)), ("Inflation / เงินเฟ้อ", str(report.inflation_count)), ("Employment / การจ้างงาน", str(report.employment_count)), ("Growth / การเติบโต", str(report.growth_count)), ("PMI-ISM / กิจกรรมเศรษฐกิจ", str(report.activity_count)), ("Aggregate Bias / มุมมองรวม", f"{report.aggregate_bias} ({report.aggregate_score})"), ("Confidence / ความมั่นใจ", str(report.confidence)), ("Intelligence Ready / พร้อมใช้งาน", str(report.intelligence_ready)), ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.execution_allowed)), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for item in report.indicators[:6]:
        rows.append((f"{item.indicator} / {item.category}", f"actual={item.actual} | forecast={item.forecast} | previous={item.previous} | surprise={item.surprise} | gold={item.gold_effect} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("gold_macro_intelligence", "Gold Macro Intelligence", "ปัญญามหภาคสำหรับทองคำ", report.status, "Converts CPI, PPI, employment, GDP, PMI, and ISM observations into structured GOLD# macro context. Macro data never executes orders directly.", "แปลงข้อมูล CPI, PPI, การจ้างงาน, GDP, PMI และ ISM เป็นบริบทมหภาคสำหรับ GOLD# โดยข้อมูลไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _central_bank_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("Observations / จำนวนข้อมูล", str(report.observation_count)), ("Hawkish / ตึงตัว", str(report.hawkish_count)), ("Dovish / ผ่อนคลาย", str(report.dovish_count)), ("Neutral / เป็นกลาง", str(report.neutral_count)), ("Policy Bias / มุมมองนโยบาย", f"{report.aggregate_policy_bias} ({report.aggregate_score})"), ("Gold Effect / ผลต่อทอง", report.aggregate_gold_effect), ("Confidence / ความมั่นใจ", str(report.confidence)), ("Intelligence Ready / พร้อมใช้งาน", str(report.intelligence_ready)), ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.execution_allowed)), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for item in report.observations[:6]:
        rows.append((f"{item.institution} / {item.communication_type}", f"speaker={item.speaker} | bias={item.policy_bias} | gold={item.gold_effect} | confidence={item.confidence} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("central_bank_intelligence", "Central Bank Intelligence", "ปัญญาธนาคารกลาง", report.status, "Classifies FOMC, ECB, BOE, BOJ, and PBOC policy communications into structured GOLD# context. Central-bank data never executes orders directly.", "จัดประเภทข้อมูลนโยบายจาก FOMC, ECB, BOE, BOJ และ PBOC เป็นบริบทแบบมีโครงสร้างสำหรับ GOLD# โดยข้อมูลไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _cot_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("Reports / จำนวนรายงาน", str(report.observation_count)), ("Bullish / สนับสนุนทอง", str(report.bullish_count)), ("Bearish / กดดันทอง", str(report.bearish_count)), ("Neutral / เป็นกลาง", str(report.neutral_count)), ("Positioning Bias / มุมมองสถานะ", f"{report.aggregate_positioning_bias} ({report.aggregate_score})"), ("Confidence / ความมั่นใจ", str(report.confidence)), ("Intelligence Ready / พร้อมใช้งาน", str(report.intelligence_ready)), ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.execution_allowed)), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for item in report.observations[:6]:
        rows.append((f"{item.market} / {item.report_id}", f"commercial_net={item.commercial_net} | noncommercial_net={item.noncommercial_net} | weekly_change={item.noncommercial_net_change} | trend={item.positioning_trend} | gold={item.gold_effect} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("cot_intelligence", "COT Intelligence", "ปัญญารายงาน COT", report.status, "Transforms supplied Commitments of Traders positioning into structured GOLD# context. COT data never executes orders directly.", "แปลงข้อมูลสถานะจากรายงาน Commitments of Traders เป็นบริบทแบบมีโครงสร้างสำหรับ GOLD# โดยข้อมูล COT ไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _open_interest_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("Observations / จำนวนข้อมูล", str(report.observation_count)), ("Rising OI / OI เพิ่ม", str(report.rising_count)), ("Falling OI / OI ลด", str(report.falling_count)), ("Stable OI / OI คงที่", str(report.stable_count)), ("Participation / การมีส่วนร่วม", report.aggregate_participation), ("Gold Effect / ผลต่อทอง", f"{report.aggregate_gold_effect} ({report.aggregate_score})"), ("Confidence / ความมั่นใจ", str(report.confidence)), ("Intelligence Ready / พร้อมใช้งาน", str(report.intelligence_ready)), ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.execution_allowed)), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for item in report.observations[:6]:
        rows.append((f"{item.market} / {item.observation_id}", f"price_change={item.price_change_pct}% | oi={item.open_interest} | oi_change={item.open_interest_change_pct}% | participation={item.participation_trend} | interpretation={item.market_interpretation} | gold={item.gold_effect} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("open_interest_intelligence", "Open Interest Intelligence", "ปัญญา Open Interest", report.status, "Transforms supplied futures open interest and price relationships into structured GOLD# participation context. Open-interest data never executes orders directly.", "แปลงความสัมพันธ์ระหว่าง Open Interest ของตลาด Futures กับราคาเป็นบริบทการมีส่วนร่วมสำหรับ GOLD# โดยข้อมูลไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _etf_flow_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("Observations / จำนวนข้อมูล", str(report.observation_count)), ("Inflows / เงินไหลเข้า", str(report.inflow_count)), ("Outflows / เงินไหลออก", str(report.outflow_count)), ("Balanced / สมดุล", str(report.neutral_count)), ("Flow Trend / แนวโน้มกระแสเงิน", report.aggregate_flow_trend), ("Gold Effect / ผลต่อทอง", f"{report.aggregate_gold_effect} ({report.aggregate_score})"), ("Daily Flow USD / กระแสรายวัน", str(report.total_daily_flow_usd)), ("Weekly Flow USD / กระแสรายสัปดาห์", str(report.total_weekly_flow_usd)), ("Confidence / ความมั่นใจ", str(report.confidence)), ("Intelligence Ready / พร้อมใช้งาน", str(report.intelligence_ready)), ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.execution_allowed)), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for item in report.observations[:6]:
        rows.append((f"{item.fund} / {item.observation_id}", f"daily={item.daily_flow_usd} | weekly={item.weekly_flow_usd} | holdings_tonnes={item.holdings_change_tonnes} | trend={item.flow_trend} | gold={item.gold_effect} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("etf_flow_intelligence", "ETF Flow Intelligence", "ปัญญากระแสเงิน ETF", report.status, "Transforms supplied GLD, IAU, and gold ETF flows into structured GOLD# context. ETF flow data never executes orders directly.", "แปลงกระแสเงินของ GLD, IAU และ Gold ETF เป็นบริบทแบบมีโครงสร้างสำหรับ GOLD# โดยข้อมูลไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _usd_index_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("Observations / จำนวนข้อมูล", str(report.observation_count)), ("Rising DXY / DXY เพิ่ม", str(report.rising_count)), ("Falling DXY / DXY ลด", str(report.falling_count)), ("Stable DXY / DXY คงที่", str(report.stable_count)), ("Divergences / ความเบี่ยงเบน", str(report.divergence_count)), ("USD Trend / แนวโน้มดอลลาร์", report.aggregate_usd_trend), ("Gold Effect / ผลต่อทอง", f"{report.aggregate_gold_effect} ({report.aggregate_score})"), ("Confidence / ความมั่นใจ", str(report.confidence)), ("Intelligence Ready / พร้อมใช้งาน", str(report.intelligence_ready)), ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.execution_allowed)), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for item in report.observations[:6]:
        rows.append((f"{item.index_name} / {item.observation_id}", f"current={item.current_value} | previous={item.previous_value} | change={item.change_pct}% | trend={item.trend} | correlation={item.gold_correlation} | divergence={item.divergence} | gold={item.gold_effect} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("usd_index_intelligence", "USD Index Intelligence", "ปัญญาดัชนีดอลลาร์สหรัฐ", report.status, "Transforms supplied DXY observations into structured GOLD# context with trend, correlation, and divergence analysis. USD index data never executes orders directly.", "แปลงข้อมูล DXY เป็นบริบทแบบมีโครงสร้างสำหรับ GOLD# พร้อมวิเคราะห์แนวโน้ม ความสัมพันธ์ และ divergence โดยข้อมูลไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _bond_yield_intelligence_panel(report: Any) -> DashboardPanel:
    rows = [("Status / สถานะ", report.status), ("Reason / เหตุผล", report.reason), ("Observations / จำนวนข้อมูล", str(report.observation_count)), ("Rising Nominal / ผลตอบแทนทั่วไปเพิ่ม", str(report.rising_nominal_count)), ("Falling Nominal / ผลตอบแทนทั่วไปลด", str(report.falling_nominal_count)), ("Rising Real Yield / Real Yield เพิ่ม", str(report.rising_real_count)), ("Falling Real Yield / Real Yield ลด", str(report.falling_real_count)), ("Inverted Curves / เส้นผลตอบแทนกลับด้าน", str(report.inverted_curve_count)), ("Yield Trend / แนวโน้มผลตอบแทน", report.aggregate_yield_trend), ("Real Yield Trend / แนวโน้ม Real Yield", report.aggregate_real_yield_trend), ("Curve Shape / รูปทรงเส้นผลตอบแทน", report.aggregate_curve_shape), ("Gold Effect / ผลต่อทอง", f"{report.aggregate_gold_effect} ({report.aggregate_score})"), ("Confidence / ความมั่นใจ", str(report.confidence)), ("Intelligence Ready / พร้อมใช้งาน", str(report.intelligence_ready)), ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.execution_allowed)), ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc)]
    for item in report.observations[:6]:
        rows.append((f"Yield / {item.observation_id}", f"US2Y={item.us2y_yield}% | US10Y={item.us10y_yield}% | real={item.real_yield}% | spread={item.curve_spread_bps}bps | curve={item.curve_shape} | nominal={item.nominal_yield_trend} | real_trend={item.real_yield_trend} | gold={item.gold_effect} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("bond_yield_intelligence", "Bond Yield Intelligence", "ปัญญาอัตราผลตอบแทนพันธบัตร", report.status, "Transforms supplied US2Y, US10Y, real-yield, and yield-curve observations into structured GOLD# context. Yield data never executes orders directly.", "แปลงข้อมูล US2Y, US10Y, real yield และเส้นอัตราผลตอบแทนเป็นบริบทแบบมีโครงสร้างสำหรับ GOLD# โดยข้อมูลไม่ส่งคำสั่งซื้อขายโดยตรง", tuple(rows))


def _market_regime_v2_panel(report: Any) -> DashboardPanel:
    rows=[("Status / สถานะ",report.status),("Reason / เหตุผล",report.reason),("Regime / ภาวะตลาด",report.regime),("Directional Bias / ทิศทาง",report.directional_bias),("Risk State / สถานะความเสี่ยง",report.risk_state),("Aggregate Score / คะแนนรวม",str(report.aggregate_score)),("Confidence / ความมั่นใจ",str(report.confidence)),("Ready Components / องค์ประกอบพร้อม",f"{report.ready_component_count}/{report.total_component_count}"),("Alignment / ความสอดคล้อง",report.component_alignment),("Intelligence Ready / พร้อมใช้งาน",str(report.intelligence_ready)),("Direct Execution / ส่งคำสั่งโดยตรง",str(report.execution_allowed)),("Next Review UTC / ตรวจสอบถัดไป",report.next_review_time_utc)]
    for item in report.components:
        rows.append((f"Component / {item.name}",f"status={item.status} | effect={item.effect} | score={item.score} | confidence={item.confidence} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("market_regime_v2","Market Regime V2","ภาวะตลาด V2",report.status,"Aggregates structured market intelligence into one explainable GOLD# regime. It never executes orders directly.","รวม Market Intelligence แบบมีโครงสร้างเป็นภาวะตลาดเดียวสำหรับ GOLD# ที่ตรวจสอบได้ และไม่ส่งคำสั่งซื้อขายโดยตรง",tuple(rows))


def _decision_intelligence_foundation_panel(report: Any) -> DashboardPanel:
    rows=[("Status / สถานะ",report.status),("Reason / เหตุผล",report.reason),("Consensus / ข้อสรุป",report.consensus),("Conflict / ความขัดแย้ง",report.conflict_state),("Opportunity / สถานะโอกาส",report.opportunity_state),("Aggregate Score / คะแนนรวม",str(report.aggregate_score)),("Confidence / ความมั่นใจ",str(report.confidence)),("Supporting / สนับสนุน",str(report.supporting_count)),("Opposing / คัดค้าน",str(report.opposing_count)),("Ready Evidence / หลักฐานพร้อม",f"{report.ready_evidence_count}/{report.total_evidence_count}"),("Market Regime / ภาวะตลาด",report.market_regime),("Regime Bias / ทิศทางภาวะตลาด",report.market_regime_bias),("Decision Ready / พร้อมตัดสินใจ",str(report.decision_ready)),("Direct Execution / ส่งคำสั่งโดยตรง",str(report.execution_allowed)),("Expected Next Action EN",report.expected_next_action_en),("Expected Next Action TH",report.expected_next_action_th),("Next Review UTC / ตรวจสอบถัดไป",report.next_review_time_utc)]
    for item in report.evidence:
        rows.append((f"Evidence / {item.source}",f"status={item.status} | direction={item.direction} | confidence={item.confidence} | weight={item.weight} | weighted={item.weighted_score} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("decision_intelligence_foundation","Decision Intelligence Foundation","รากฐานปัญญาการตัดสินใจ",report.status,"Resolves structured consensus and conflicts before any entry validation. It never executes orders directly.","สรุปฉันทามติและแก้ความขัดแย้งของข้อมูลแบบมีโครงสร้างก่อนตรวจสอบการเข้าออเดอร์ และไม่ส่งคำสั่งซื้อขายโดยตรง",tuple(rows))


def _consensus_engine_panel(report: Any) -> DashboardPanel:
    rows=[("Consensus / ฉันทามติ",report.consensus),("Consensus Quality / คุณภาพฉันทามติ",report.consensus_quality),("Agreement Ratio / สัดส่วนเห็นพ้อง",f"{report.agreement_ratio:.2%}"),("Conflict Ratio / สัดส่วนขัดแย้ง",f"{report.conflict_ratio:.2%}"),("BUY Score",str(report.buy_score)),("SELL Score",str(report.sell_score)),("WAIT Score",str(report.neutral_score)),("Dominant Sources / แหล่งข้อมูลหลัก",", ".join(report.dominant_sources) or "-"),("Contradicting Sources / แหล่งข้อมูลขัดแย้ง",", ".join(report.contradicting_sources) or "-"),("Expected Next Action EN",report.expected_next_action_en),("การดำเนินการถัดไป TH",report.expected_next_action_th),("Direct Execution",str(report.direct_execution))]
    return DashboardPanel("consensus_engine","Consensus Engine","กลไกฉันทามติ",report.status,"Calculates weighted agreement and conflict across structured evidence before trade scoring.","คำนวณน้ำหนักการเห็นพ้องและความขัดแย้งของหลักฐานแบบมีโครงสร้างก่อนให้คะแนนโอกาสซื้อขาย",tuple(rows))


def _conflict_resolver_panel(report: Any) -> DashboardPanel:
    rows = (
        ("Status", str(report.status)),
        ("Original Consensus", str(report.original_consensus)),
        ("Resolved Consensus", str(report.resolved_consensus)),
        ("Conflict Level", str(report.conflict_level)),
        ("Conflict Score", str(report.conflict_score)),
        ("Resolution Method", str(report.resolution_method)),
        ("Unresolved Sources", ", ".join(report.unresolved_sources) or "None"),
        ("Waiting Reason EN", report.waiting_reason_en),
        ("Waiting Reason TH", report.waiting_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review Time", report.next_review_time_utc),
        ("Direct Execution", str(report.direct_execution)),
    )
    return DashboardPanel("conflict_resolver", "Conflict Resolver", "ตัวแก้ความขัดแย้ง", report.status, "Resolves material evidence disagreement before scoring or execution review.", "แก้ความขัดแย้งของหลักฐานสำคัญก่อนการให้คะแนนหรือทบทวนการส่งคำสั่ง", rows)


def _opportunity_ranking_panel(report: Any) -> DashboardPanel:
    rows = [
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Top Opportunity / โอกาสอันดับหนึ่ง", report.top_opportunity_id),
        ("Top Direction / ทิศทางอันดับหนึ่ง", report.top_direction),
        ("Top Score / คะแนนอันดับหนึ่ง", str(report.top_score)),
        ("Eligible / ผ่านเกณฑ์", f"{report.eligible_count}/{report.opportunity_count}"),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.direct_execution)),
    ]
    for item in report.ranked_opportunities[:10]:
        rows.append((f"Rank {item.rank} / {item.opportunity_id}", f"symbol={item.symbol} | direction={item.direction} | score={item.total_score} | eligible={item.eligible} | EN: {item.block_reason_en} | TH: {item.block_reason_th}"))
    return DashboardPanel("opportunity_ranking", "Opportunity Ranking Engine", "กลไกจัดอันดับโอกาส", report.status, "Ranks eligible GOLD# opportunities after regime, consensus, conflict, risk, and cost review. Ranking never executes orders.", "จัดอันดับโอกาส GOLD# หลังตรวจ Market Regime ฉันทามติ ความขัดแย้ง ความเสี่ยง และต้นทุน โดยการจัดอันดับไม่ส่งคำสั่งซื้อขาย", tuple(rows))


def _trade_scoring_panel(report: Any) -> DashboardPanel:
    rows = [
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Top Opportunity / โอกาสอันดับหนึ่ง", report.top_opportunity_id),
        ("Top Direction / ทิศทางอันดับหนึ่ง", report.top_direction),
        ("Top Final Score / คะแนนสุดท้ายสูงสุด", str(report.top_final_score)),
        ("Top Grade / เกรดสูงสุด", report.top_grade),
        ("Eligible / ผ่านเกณฑ์", f"{report.eligible_count}/{report.score_count}"),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.direct_execution)),
    ]
    for item in report.scores[:10]:
        rows.append((f"{item.opportunity_id} / {item.grade}", f"direction={item.direction} | final={item.final_score} | opportunity={item.opportunity_score} | quality={item.quality_score} | risk_adjusted={item.risk_adjusted_score} | execution={item.execution_readiness_score} | eligible={item.eligible} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("trade_scoring", "Trade Scoring Engine", "กลไกให้คะแนนการซื้อขาย", report.status, "Scores ranked GOLD# opportunities using deterministic quality, risk-adjusted, and execution-readiness factors. Scoring never executes orders.", "ให้คะแนนโอกาส GOLD# ที่จัดอันดับแล้วด้วยปัจจัยคุณภาพ ปรับตามความเสี่ยง และความพร้อมในการดำเนินการแบบกำหนดแน่นอน โดยคะแนนไม่ส่งคำสั่งซื้อขาย", tuple(rows))


def _unit_allocation_panel(report: Any) -> DashboardPanel:
    rows = [
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Profile / โปรไฟล์", report.profile_name),
        ("Selected Opportunity / โอกาสที่เลือก", report.selected_opportunity_id),
        ("Direction / ทิศทาง", report.selected_direction),
        ("Allocated Units / จำนวน Unit", str(report.allocated_units)),
        ("Lot per Unit / Lot ต่อ Unit", str(report.lot_per_unit)),
        ("Total Lot / Lot รวม", str(report.total_lot)),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.direct_execution)),
    ]
    for item in report.allocations[:10]:
        rows.append((f"{item.opportunity_id} / {item.trade_grade}", f"direction={item.direction} | score={item.trade_score} | capital_per_unit={item.capital_per_unit} | capital_units={item.capital_max_units} | profile_units={item.profile_max_units} | score_units={item.score_max_units} | allocated={item.allocated_units} | total_lot={item.total_lot} | eligible={item.eligible} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("unit_allocation", "Unit Allocation Engine", "กลไกจัดสรร Unit", report.status, "Allocates fixed 0.01-lot units from profile, capital, risk, and trade score. It never increases lot per unit and never executes orders.", "จัดสรร Unit คงที่ 0.01 lot จากโปรไฟล์ เงินทุน ความเสี่ยง และคะแนนการซื้อขาย โดยไม่เพิ่ม lot ต่อ Unit และไม่ส่งคำสั่งซื้อขาย", tuple(rows))


def _entry_validation_panel(report: Any) -> DashboardPanel:
    rows = [
        ("Status / สถานะ", report.status),
        ("Reason / เหตุผล", report.reason),
        ("Selected Opportunity / โอกาสที่เลือก", report.selected_opportunity_id),
        ("Direction / ทิศทาง", report.selected_direction),
        ("Entry Approved / อนุมัติจุดเข้า", str(report.entry_approved)),
        ("Approved Units / Unit ที่อนุมัติ", str(report.approved_units)),
        ("Lot per Unit / Lot ต่อ Unit", str(report.lot_per_unit)),
        ("Total Lot / Lot รวม", str(report.total_lot)),
        ("Waiting Reason EN", report.waiting_reason_en),
        ("Waiting Reason TH", report.waiting_reason_th),
        ("Expected Next Action EN", report.expected_next_action_en),
        ("Expected Next Action TH", report.expected_next_action_th),
        ("Next Review UTC / ตรวจสอบถัดไป", report.next_review_time_utc),
        ("Direct Execution / ส่งคำสั่งโดยตรง", str(report.direct_execution)),
    ]
    for item in report.validations[:10]:
        rows.append((f"{item.opportunity_id} / {item.direction}", f"approved={item.approved} | units={item.allocated_units} | regime={item.market_regime_ready} | conflict={item.conflict_allowed} | score={item.trade_score_allowed} | risk={item.risk_allowed} | timing={item.timing_allowed} | spread={item.spread_allowed} | allocation={item.allocation_allowed} | blocks={','.join(item.block_reasons)} | EN: {item.explanation_en} | TH: {item.explanation_th}"))
    return DashboardPanel("entry_validation", "Entry Validation Engine", "กลไกตรวจสอบจุดเข้า", report.status, "Validates regime, conflict, score, risk, timing, spread, and fixed-unit allocation before paper/demo execution review. Validation never sends orders.", "ตรวจสอบ Market Regime ความขัดแย้ง คะแนน ความเสี่ยง เวลา Spread และการจัดสรร Unit คงที่ก่อน paper/demo execution โดยไม่ส่งคำสั่งซื้อขาย", tuple(rows))
