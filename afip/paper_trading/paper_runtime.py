"""Paper trading runtime for Production Milestone G Pack 6."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .paper_observation import PaperTradingObservation
from .paper_policy import PaperTradingPolicy
from .paper_profile import PaperTradingProfile
from .paper_report import PaperTradingReport
from .paper_repository import PaperTradingRepository
from .paper_models import PaperOrder, PaperOrderState, PaperPortfolioReport

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
UNIT_LOT = 0.01


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


class PaperTradingRuntime:
    """Evaluates paper trading readiness without creating live orders."""

    def __init__(self, policy: PaperTradingPolicy | None = None, repository: PaperTradingRepository | None = None) -> None:
        self.policy = policy or PaperTradingPolicy()
        self.repository = repository or PaperTradingRepository()

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperTradingProfile:
        observation = PaperTradingObservation.from_mapping(record)
        reason = self.policy.evaluate_reason(observation)
        status = self.policy.status_for(observation)
        profile = PaperTradingProfile.from_observation(observation, status=status, reason=reason)
        self.repository.append(profile)
        return profile

    def evaluate_many(self, records: Iterable[Mapping[str, Any]]) -> list[PaperTradingProfile]:
        return [self.evaluate_one(record) for record in records]

    def explain_one(self, record: Mapping[str, Any]) -> PaperTradingReport:
        return PaperTradingReport(self.evaluate_one(record))

    def explain_many(self, records: Iterable[Mapping[str, Any]]) -> list[PaperTradingReport]:
        return [self.explain_one(record) for record in records]


def _state(state: str, reason: str, confidence: float, risk_status: str, action: str) -> PaperOrderState:
    thai = {
        "WAITING": "รอเงื่อนไขครบก่อนเปิดคำสั่งจำลอง",
        "READY": "พร้อมเปิดคำสั่งจำลองเมื่อผ่านนโยบาย",
        "OPENED": "เปิดสถานะจำลองแล้วโดยไม่ส่งคำสั่งจริง",
        "MANAGING": "กำลังบริหารสถานะจำลองตามความเสี่ยง",
        "BREAK_EVEN": "พิจารณาคุ้มครองทุนด้วยจุดคุ้มทุน",
        "TRAILING": "ติดตามกำไรด้วย Trailing Stop จำลอง",
        "PARTIAL_CLOSE": "พิจารณาปิดบางส่วนผ่าน Unit จำลอง",
        "EXIT_READY": "พร้อมปิดสถานะจำลองเมื่อเหตุผลครบ",
        "CLOSED": "ปิดสถานะจำลองและบันทึกผลแล้ว",
    }.get(state, "สถานะคำสั่งจำลอง")
    english = {
        "WAITING": "Waiting for all paper-trading conditions before simulated entry.",
        "READY": "Ready for simulated entry after policy approval.",
        "OPENED": "Simulated position opened without broker execution.",
        "MANAGING": "Managing simulated position with risk controls.",
        "BREAK_EVEN": "Reviewing capital protection using simulated break-even.",
        "TRAILING": "Protecting profit through simulated trailing stop.",
        "PARTIAL_CLOSE": "Reviewing simulated partial close by units.",
        "EXIT_READY": "Ready for simulated exit when exit reasons are complete.",
        "CLOSED": "Simulated position closed and recorded.",
    }.get(state, "Paper order state.")
    return PaperOrderState(state, thai, english, reason, action, round(confidence, 2), risk_status, "next_runtime_cycle")


def _lifecycle(status: str, reason: str, confidence: float, risk_status: str) -> tuple[PaperOrderState, ...]:
    sequence = ("WAITING", "READY", "OPENED", "MANAGING", "BREAK_EVEN", "TRAILING", "PARTIAL_CLOSE", "EXIT_READY", "CLOSED")
    normalized = status if status in sequence else "WAITING"
    end = sequence.index(normalized)
    return tuple(_state(item, reason, confidence, risk_status, "continue_paper_review") for item in sequence[: end + 1])


class PaperTradingEngineRuntime:
    """Evaluate paper orders and portfolio without live execution."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PaperPortfolioReport:
        broker = _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        profile_name = _clean(record.get("profile_name", "Balanced"), "Balanced")
        mode = _upper(record.get("mode", "PAPER"), "PAPER")
        maximum_units = max(1, _int(record.get("maximum_units", 1), 1))
        initial_balance = _float(record.get("paper_balance", record.get("initial_capital", 1000.0)), 1000.0)
        reserve = _float(record.get("reserve", 0.0), 0.0)
        raw_orders = _records(record.get("paper_orders", record.get("orders", ())))
        validation_items: list[str] = []
        if broker != VERSION1_BROKER:
            validation_items.append("version1_xm_only_required")
        if symbol != VERSION1_SYMBOL:
            validation_items.append("version1_gold_only_required")
        if mode == "LIVE" or bool(record.get("live_execution_enabled", False)):
            validation_items.append("live_execution_blocked_for_paper_trading")
        if not record.get("paper_trading_requested", bool(raw_orders)):
            validation_items.append("paper_trading_not_requested")
        orders: list[PaperOrder] = []
        for index, item in enumerate(raw_orders, start=1):
            units = max(1, min(maximum_units, _int(item.get("units", 1), 1)))
            side = _upper(item.get("side", item.get("action", "BUY")), "BUY")
            status = _upper(item.get("status", "WAITING"), "WAITING").replace(" ", "_")
            entry_price = _float(item.get("entry_price", item.get("price", 0.0)), 0.0)
            current_price = _float(item.get("current_price", entry_price), entry_price)
            point_value = _float(item.get("point_value", 1.0), 1.0)
            direction = 1.0 if side == "BUY" else -1.0
            floating_profit = _float(item.get("floating_profit", (current_price - entry_price) * direction * units * point_value), 0.0)
            closed_profit = _float(item.get("closed_profit", 0.0), 0.0)
            confidence = _float(item.get("confidence", record.get("confidence", 0.0)), 0.0)
            risk_status = _clean(item.get("risk_status", record.get("risk_status", "risk_review")), "risk_review")
            reason = _clean(item.get("reason", item.get("current_ai_reasoning", "paper_order_waiting_for_verified_runtime_conditions")), "paper_order_waiting_for_verified_runtime_conditions")
            orders.append(PaperOrder(
                order_id=_clean(item.get("order_id", f"PAPER-{index:04d}"), f"PAPER-{index:04d}"), symbol=symbol, side=side,
                units=units, lot_per_unit=UNIT_LOT, total_lot=round(units * UNIT_LOT, 2), status=status,
                entry_price=entry_price, current_price=current_price, stop_loss=_float(item.get("stop_loss", 0.0), 0.0), take_profit=_float(item.get("take_profit", 0.0), 0.0),
                floating_profit=round(floating_profit, 2), closed_profit=round(closed_profit, 2), quality=_clean(item.get("quality", "review"), "review"), confidence=round(confidence, 2),
                waiting_reason=_clean(item.get("waiting_reason", reason), reason), entry_reason=_clean(item.get("entry_reason", "entry_requires_policy_risk_and_market_regime_alignment"), "entry_requires_policy_risk_and_market_regime_alignment"),
                holding_reason=_clean(item.get("holding_reason", "hold_while_market_reason_and_risk_remain_valid"), "hold_while_market_reason_and_risk_remain_valid"), stop_loss_reason=_clean(item.get("stop_loss_reason", "stop_loss_review_protects_capital_per_profile_risk"), "stop_loss_review_protects_capital_per_profile_risk"),
                break_even_reason=_clean(item.get("break_even_reason", "break_even_only_after_protection_condition_is_met"), "break_even_only_after_protection_condition_is_met"), trailing_reason=_clean(item.get("trailing_reason", "trailing_only_after_profit_protection_is_justified"), "trailing_only_after_profit_protection_is_justified"),
                partial_close_reason=_clean(item.get("partial_close_reason", "partial_close_uses_units_not_direct_lot_increase"), "partial_close_uses_units_not_direct_lot_increase"), exit_reason=_clean(item.get("exit_reason", "exit_waits_for_complete_exit_reason"), "exit_waits_for_complete_exit_reason"),
                alternative_decision=_clean(item.get("alternative_decision", "wait_and_reassess"), "wait_and_reassess"), current_ai_reasoning=reason, expected_next_action=_clean(item.get("expected_next_action", "continue_paper_trading_review"), "continue_paper_trading_review"),
                risk_status=risk_status, estimated_next_review=_clean(item.get("estimated_next_review", "next_runtime_cycle"), "next_runtime_cycle"), lifecycle=_lifecycle(status, reason, confidence, risk_status)))
        floating = round(sum(order.floating_profit for order in orders if order.status != "CLOSED"), 2)
        closed = round(sum(order.closed_profit for order in orders), 2)
        equity = round(initial_balance + floating + closed, 2)
        allocation = round(max(0.0, equity - reserve), 2)
        roi = round(((equity - initial_balance) / initial_balance * 100.0), 2) if initial_balance else 0.0
        current_units = sum(order.units for order in orders if order.status not in {"CLOSED", "WAITING"})
        counts = {"WAITING": 0, "READY": 0, "OPENED": 0, "MANAGING": 0, "CLOSED": 0}
        for order in orders:
            counts[order.status if order.status in counts else "MANAGING"] += 1
        if broker != VERSION1_BROKER or symbol != VERSION1_SYMBOL:
            status, reason = "BLOCKED", "paper_trading_blocked_by_version1_policy"
        elif "live_execution_blocked_for_paper_trading" in validation_items:
            status, reason = "BLOCKED", "paper_trading_blocks_live_execution"
        elif "paper_trading_not_requested" in validation_items:
            status, reason = "READY", "paper_trading_not_requested"
        elif not orders:
            status, reason = "WAITING", "paper_trading_waiting_for_orders"
        else:
            status, reason = "READY", "paper_trading_runtime_ready"
        return PaperPortfolioReport(status, reason, broker, symbol, profile_name, "PAPER", round(initial_balance + closed, 2), equity, round(reserve, 2), allocation, roi, floating, closed, current_units, maximum_units, UNIT_LOT, len(orders), counts["WAITING"], counts["READY"], counts["OPENED"], counts["MANAGING"], counts["CLOSED"], tuple(orders), ("paper_trading", "order_center", "afip_bank", "unit_allocation", "order_explainability", "risk_status", "expected_next_action"), tuple(validation_items))

    def explain_one(self, record: Mapping[str, Any]) -> PaperPortfolioReport:
        return self.evaluate_one(record)
