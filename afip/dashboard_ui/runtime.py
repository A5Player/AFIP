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
