"""Research Center runtime for Milestone H Pack 6."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .research_models import ResearchCenterReport, ResearchMetricRow, ResearchStatisticGroup

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
MINIMUM_RESEARCH_ORDERS = 100
STANDARD_PROMOTION_ORDERS = 1000


def _clean(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _clean(value, default).upper()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _records(raw: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(raw, Mapping):
        return (raw,)
    if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
        return tuple(item for item in raw if isinstance(item, Mapping))
    return ()


def _is_research(record: Mapping[str, Any]) -> bool:
    scope = _upper(record.get("statistic_scope", record.get("scope", "RESEARCH")), "RESEARCH")
    return scope in {"RESEARCH", "RESEARCH_ONLY", "WALK_FORWARD", "PAPER_RESEARCH"}


def _score(win_rate: float, profit_factor: float, expectancy: float, drawdown: float, risk_score: float, sample_size: int) -> float:
    sample_weight = min(1.0, sample_size / MINIMUM_RESEARCH_ORDERS)
    raw = (win_rate * 0.30) + (min(profit_factor, 5.0) * 12.0) + (expectancy * 8.0) - (drawdown * 1.5) - (risk_score * 2.0)
    return round(max(0.0, raw * sample_weight), 2)


def _group(records: tuple[Mapping[str, Any], ...], field: str, name: str, thai_name: str) -> ResearchStatisticGroup:
    bucket: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        bucket[_clean(record.get(field, "UNKNOWN"), "UNKNOWN")].append(record)
    rows: list[ResearchMetricRow] = []
    for category_value, items in bucket.items():
        sample_size = len(items)
        wins = sum(1 for item in items if _float(item.get("profit", item.get("net_profit", 0.0))) > 0.0)
        losses = sum(1 for item in items if _float(item.get("profit", item.get("net_profit", 0.0))) < 0.0)
        gross_profit = sum(max(0.0, _float(item.get("profit", item.get("net_profit", 0.0)))) for item in items)
        gross_loss = abs(sum(min(0.0, _float(item.get("profit", item.get("net_profit", 0.0)))) for item in items))
        win_rate = round((wins / sample_size * 100.0), 2) if sample_size else 0.0
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss else round(gross_profit, 2)
        expectancy = round(sum(_float(item.get("profit", item.get("net_profit", 0.0))) for item in items) / max(1, sample_size), 2)
        drawdown = round(max((_float(item.get("drawdown", 0.0)) for item in items), default=0.0), 2)
        risk_score = round(sum(_float(item.get("risk_score", 1.0), 1.0) for item in items) / max(1, sample_size), 2)
        rows.append(
            ResearchMetricRow(
                rank=0,
                category=field,
                name=category_value,
                sample_size=sample_size,
                win_rate=win_rate,
                profit_factor=profit_factor,
                expectancy=expectancy,
                drawdown=drawdown,
                risk_score=risk_score,
                score=_score(win_rate, profit_factor, expectancy, drawdown, risk_score, sample_size),
                thai_description=f"สถิติวิจัยสำหรับ {category_value} แยกจากข้อมูล Live",
                english_description=f"Research-only statistics for {category_value}, separated from live statistics.",
            )
        )
    ranked = sorted(rows, key=lambda row: (row.score, row.sample_size), reverse=True)[:10]
    ranked = [ResearchMetricRow(index + 1, row.category, row.name, row.sample_size, row.win_rate, row.profit_factor, row.expectancy, row.drawdown, row.risk_score, row.score, row.thai_description, row.english_description) for index, row in enumerate(ranked)]
    return ResearchStatisticGroup(name=name, thai_name=thai_name, english_description=f"Top 10 {name.replace('_', ' ')} using research-only completed orders.", statistic_scope="RESEARCH_ONLY", rows=tuple(ranked))


class ResearchCenterRuntime:
    """Build separated research analytics for dashboard and standard learning."""

    def evaluate_one(self, record: Mapping[str, Any]) -> ResearchCenterReport:
        broker = _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        profile_name = _clean(record.get("profile_name", "Research"), "Research")
        profile_type = _upper(record.get("profile_type", profile_name), profile_name.upper())
        raw_records = _records(record.get("research_orders", record.get("completed_orders", ())))
        research_records = tuple(item for item in raw_records if _is_research(item))
        research_requested = bool(record.get("research_center_requested", record.get("research_mode", bool(raw_records))))
        completed_orders = _int(record.get("completed_research_orders", len(research_records)), len(research_records))
        validation_items: list[str] = []
        if broker != VERSION1_BROKER:
            validation_items.append("version1_xm_only_required")
        if symbol != VERSION1_SYMBOL:
            validation_items.append("version1_gold_only_required")
        if research_requested and not record.get("historical_research_ready", record.get("research_ready", False)):
            validation_items.append("historical_research_dataset_required")
        if research_requested and completed_orders < MINIMUM_RESEARCH_ORDERS:
            validation_items.append("minimum_100_research_orders_required")
        research_ready = broker == VERSION1_BROKER and symbol == VERSION1_SYMBOL and "historical_research_dataset_required" not in validation_items
        walk_forward_ready = bool(record.get("walk_forward_ready", False)) and research_ready
        standard_learning_candidate = research_requested and completed_orders >= MINIMUM_RESEARCH_ORDERS and research_ready
        if broker != VERSION1_BROKER or symbol != VERSION1_SYMBOL:
            status, reason = "BLOCKED", "research_center_blocked_by_version1_policy"
        elif not research_requested:
            status, reason = "READY", "research_center_not_requested"
        elif not research_ready:
            status, reason = "WAITING", "research_center_waiting_for_historical_research_dataset"
        elif completed_orders < MINIMUM_RESEARCH_ORDERS:
            status, reason = "WAITING", "research_center_waiting_for_100_completed_research_orders"
        else:
            status, reason = "READY", "research_center_ready"
        groups = {
            "top_trading_hours": _group(research_records, "trading_hour", "top_trading_hours", "10 อันดับชั่วโมงเทรด"),
            "top_trading_sessions": _group(research_records, "trading_session", "top_trading_sessions", "10 อันดับช่วงตลาด"),
            "top_market_regimes": _group(research_records, "market_regime", "top_market_regimes", "10 อันดับภาวะตลาด"),
            "top_entry_plans": _group(research_records, "entry_plan", "top_entry_plans", "10 อันดับแผนเข้า"),
            "top_exit_plans": _group(research_records, "exit_plan", "top_exit_plans", "10 อันดับแผนออก"),
            "top_patterns": _group(research_records, "pattern", "top_patterns", "10 อันดับรูปแบบ"),
            "top_engine_combinations": _group(research_records, "engine_combination", "top_engine_combinations", "10 อันดับชุดเครื่องมือวิเคราะห์"),
            "top_profit_reasons": _group(tuple(item for item in research_records if _float(item.get("profit", item.get("net_profit", 0.0))) > 0.0), "profit_reason", "top_profit_reasons", "10 อันดับเหตุผลกำไร"),
            "top_loss_reasons": _group(tuple(item for item in research_records if _float(item.get("profit", item.get("net_profit", 0.0))) < 0.0), "loss_reason", "top_loss_reasons", "10 อันดับเหตุผลขาดทุน"),
        }
        return ResearchCenterReport(
            status=status,
            reason=reason,
            profile_name=profile_name,
            profile_type=profile_type,
            broker=broker,
            symbol=symbol,
            research_scope="RESEARCH_ONLY",
            live_scope="LIVE_SEPARATE_NOT_USED_FOR_RESEARCH_RANKING",
            minimum_orders_required=MINIMUM_RESEARCH_ORDERS,
            completed_research_orders=completed_orders,
            research_ready=research_ready,
            walk_forward_ready=walk_forward_ready,
            standard_learning_candidate=standard_learning_candidate,
            standard_learning_policy="temporary_standard_every_100_orders_permanent_standard_every_1000_orders_only_if_quality_improves",
            dashboard_sections=("research_statistics", "live_statistics_separate", "top_10_rankings", "standard_learning", "walk_forward_readiness"),
            validation_items=tuple(validation_items),
            **groups,
        )

    def explain_one(self, record: Mapping[str, Any]) -> ResearchCenterReport:
        return self.evaluate_one(record)
