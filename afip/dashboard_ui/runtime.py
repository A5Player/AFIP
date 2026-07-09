"""Visible Dashboard UI runtime for Production Milestone H Pack 8."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Mapping

from afip.dashboard_center import DashboardFoundationRuntime, DashboardRuntimeStatus
from afip.paper_trading import PaperTradingEngineRuntime
from afip.research_center import ResearchCenterRuntime

from .models import DashboardPanel, DashboardUIReport


VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
_ALLOWED_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}


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
            _intelligence_panel(record),
            _trading_panel(paper),
            _analytics_panel(research),
            _bank_panel(paper),
            _research_panel(research),
            _system_panel(record, runtime),
            _market_panel(record),
            _order_center_panel(paper),
        )
        if validation_items:
            panels = (_policy_panel(validation_items),) + panels
        return DashboardUIReport(
            status=status,
            reason=reason,
            page_title="AFIP Dashboard — Milestone H Pack 8",
            profile_name=profile_name,
            broker=broker,
            symbol=symbol,
            mode=mode,
            live_execution_enabled=False,
            panels=panels,
            navigation_sections=("Runtime", "Intelligence", "Trading", "Analytics", "AFIP Bank", "Research", "System", "Market", "Order Center"),
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


def _bank_panel(paper: Any) -> DashboardPanel:
    return DashboardPanel("afip_bank", "AFIP Bank", "ธนาคาร AFIP", paper.status, "Displays paper balance, equity, reserve, ROI, and allocation.", "แสดง Balance, Equity, Reserve, ROI และ Allocation", (
        ("Balance", str(paper.balance)),
        ("Equity", str(paper.equity)),
        ("Reserve", str(paper.reserve)),
        ("Allocation", str(paper.allocation)),
        ("ROI", f"{paper.roi}%"),
        ("Floating Profit", str(paper.floating_profit)),
        ("Closed Profit", str(paper.closed_profit)),
    ))


def _research_panel(research: Any) -> DashboardPanel:
    groups = ("Top 10 Trading Hours", "Top 10 Trading Sessions", "Top 10 Market Regimes", "Top 10 Entry Plans", "Top 10 Exit Plans", "Top 10 Patterns", "Top 10 Engine Combinations", "Top 10 Profit Reasons", "Top 10 Loss Reasons")
    return DashboardPanel("research", "Research Center", "ศูนย์วิจัย", research.status, "Displays required research groups.", "แสดงกลุ่มสถิติวิจัยที่จำเป็น", tuple((group, "available") for group in groups))


def _system_panel(record: Mapping[str, Any], runtime: Any) -> DashboardPanel:
    return DashboardPanel("system", "Dashboard System", "ระบบ", runtime.status, "Displays VPS and connectivity status.", "แสดงสถานะ VPS และการเชื่อมต่อ", (
        ("Internet Status", _text(record.get("internet_status", "READY"), "READY")),
        ("MT5 Status", runtime.connection_status),
        ("Broker Status", _text(record.get("broker_status", "READY"), "READY")),
        ("CPU", _text(record.get("cpu", "not_collected_yet"), "not_collected_yet")),
        ("RAM", _text(record.get("ram", "not_collected_yet"), "not_collected_yet")),
        ("Disk", _text(record.get("disk", "not_collected_yet"), "not_collected_yet")),
    ))


def _market_panel(record: Mapping[str, Any]) -> DashboardPanel:
    return DashboardPanel("market", "Dashboard Market", "ตลาด", "READY", "Displays market session and open/close status.", "แสดงสถานะตลาดและช่วงเวลาเทรด", (
        ("Market Open / Close", _text(record.get("market_status", "market_status_pending_live_calendar"), "market_status_pending_live_calendar")),
        ("Trading Session", _text(record.get("trading_session", "session_pending_runtime_clock"), "session_pending_runtime_clock")),
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


def _panel_html(panel: DashboardPanel) -> str:
    rows = "\n".join(f"<tr><td>{escape(key)}</td><td>{escape(value)}</td></tr>" for key, value in panel.rows)
    return f"""<section id=\"{escape(panel.panel_id)}\">
<h2>{escape(panel.title_en)} / {escape(panel.title_th)}</h2>
<p class=\"status\">{escape(panel.status)}</p>
<p>{escape(panel.description_en)}<br><small>{escape(panel.description_th)}</small></p>
<table>{rows}</table>
</section>"""
