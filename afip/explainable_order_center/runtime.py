"""Explainable Order Center runtime for Production Bring-up Pack 5."""

from __future__ import annotations

from typing import Any, Mapping

from .models import BilingualExplanation, ExplainableOrderCenterReport, ExplainableOrderItem

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
UNIT_LOT = 0.01

_EXPLANATION_TEXT: dict[str, tuple[str, str, str, str]] = {
    "waiting_reason": (
        "Waiting Reason",
        "เหตุผลที่รอ",
        "Explains why AFIP is waiting before opening or changing an order.",
        "อธิบายเหตุผลที่ AFIP ยังรอก่อนเปิดหรือปรับคำสั่ง",
    ),
    "entry_reason": (
        "Entry Reason",
        "เหตุผลการเข้าเทรด",
        "Explains the verified market, policy, confidence, and risk reason behind a simulated entry.",
        "อธิบายเหตุผลด้านตลาด นโยบาย ความมั่นใจ และความเสี่ยงก่อนเข้าเทรดจำลอง",
    ),
    "holding_reason": (
        "Holding Reason",
        "เหตุผลการถือสถานะ",
        "Explains why the current simulated position remains valid to hold.",
        "อธิบายว่าทำไมสถานะจำลองปัจจุบันยังสมควรถือต่อ",
    ),
    "stop_loss_move_reason": (
        "Stop Loss Move Reason",
        "เหตุผลการเลื่อน Stop Loss",
        "Explains why the protective stop should stay or move according to risk protection rules.",
        "อธิบายว่าทำไม Stop Loss ควรคงเดิมหรือเลื่อนตามกฎคุ้มครองความเสี่ยง",
    ),
    "take_profit_change_reason": (
        "Take Profit Change Reason",
        "เหตุผลการปรับ Take Profit",
        "Explains why the simulated target should stay or be reviewed.",
        "อธิบายว่าทำไมเป้าหมายจำลองควรคงเดิมหรือถูกทบทวน",
    ),
    "trailing_stop_reason": (
        "Trailing Stop Reason",
        "เหตุผล Trailing Stop",
        "Explains whether profit protection through a simulated trailing stop is justified.",
        "อธิบายว่าการคุ้มครองกำไรด้วย Trailing Stop จำลองมีเหตุผลเพียงพอหรือไม่",
    ),
    "partial_close_reason": (
        "Partial Close Reason",
        "เหตุผลการปิดบางส่วน",
        "Explains simulated partial close decisions by unit count instead of direct lot increase.",
        "อธิบายการปิดบางส่วนแบบจำลองด้วยจำนวน Unit ไม่ใช่เพิ่ม Lot ตรง ๆ",
    ),
    "exit_reason": (
        "Exit Reason",
        "เหตุผลการออกจากสถานะ",
        "Explains the conditions required before AFIP considers a simulated exit complete.",
        "อธิบายเงื่อนไขที่ต้องครบก่อน AFIP พิจารณาออกจากสถานะจำลอง",
    ),
    "expected_next_action": (
        "Expected Next Action",
        "การกระทำถัดไปที่คาดไว้",
        "Shows the next safe review step AFIP expects to perform.",
        "แสดงขั้นตอนตรวจสอบถัดไปที่ปลอดภัยซึ่ง AFIP คาดว่าจะทำ",
    ),
    "confidence": (
        "Confidence",
        "ความมั่นใจ",
        "Displays the current decision confidence used for review and monitoring.",
        "แสดงค่าความมั่นใจปัจจุบันที่ใช้สำหรับตรวจสอบและติดตาม",
    ),
    "risk": (
        "Risk",
        "ความเสี่ยง",
        "Shows the current risk state before any simulated order management action.",
        "แสดงสถานะความเสี่ยงปัจจุบันก่อนการบริหารคำสั่งจำลอง",
    ),
    "next_review_time": (
        "Next Review Time",
        "เวลาตรวจสอบครั้งถัดไป",
        "Shows when AFIP should review the order again.",
        "แสดงเวลาที่ AFIP ควรกลับมาตรวจสอบคำสั่งอีกครั้ง",
    ),
}

_FIELDS = tuple(_EXPLANATION_TEXT.keys())


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


def _order_records(raw: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(raw, Mapping):
        return (raw,)
    if isinstance(raw, (str, bytes)):
        return ()
    try:
        return tuple(item for item in raw if isinstance(item, Mapping))
    except TypeError:
        return ()


def _value_for(field: str, order: Mapping[str, Any], confidence: float, risk_status: str, next_review: str) -> str:
    if field == "stop_loss_move_reason":
        return _clean(order.get("stop_loss_move_reason", order.get("stop_loss_reason", "stop_loss_review_protects_capital_per_profile_risk")), "stop_loss_review_protects_capital_per_profile_risk")
    if field == "take_profit_change_reason":
        return _clean(order.get("take_profit_change_reason", order.get("take_profit_reason", "take_profit_review_waits_for_verified_target_reason")), "take_profit_review_waits_for_verified_target_reason")
    if field == "trailing_stop_reason":
        return _clean(order.get("trailing_stop_reason", order.get("trailing_reason", "trailing_only_after_profit_protection_is_justified")), "trailing_only_after_profit_protection_is_justified")
    if field == "risk":
        return risk_status
    if field == "confidence":
        return str(round(confidence, 2))
    if field == "next_review_time":
        return next_review
    defaults = {
        "waiting_reason": "waiting_for_complete_runtime_review",
        "entry_reason": "entry_requires_policy_risk_and_market_regime_alignment",
        "holding_reason": "hold_while_market_reason_and_risk_remain_valid",
        "partial_close_reason": "partial_close_uses_units_not_direct_lot_increase",
        "exit_reason": "exit_waits_for_complete_exit_reason",
        "expected_next_action": "continue_paper_trading_review",
    }
    return _clean(order.get(field, defaults.get(field, "review_required")), defaults.get(field, "review_required"))


class ExplainableOrderCenterRuntime:
    """Build a bilingual order explanation report without enabling execution."""

    def evaluate_one(self, record: Mapping[str, Any]) -> ExplainableOrderCenterReport:
        broker = _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        live_execution_enabled = bool(record.get("live_execution_enabled", False)) or _upper(record.get("mode", "PAPER"), "PAPER") == "LIVE"
        raw_orders = _order_records(record.get("paper_orders", record.get("orders", ())))
        maximum_units = max(1, _int(record.get("maximum_units", 1), 1))
        items: list[ExplainableOrderItem] = []
        for index, order in enumerate(raw_orders, start=1):
            units = max(1, min(maximum_units, _int(order.get("units", 1), 1)))
            confidence = _float(order.get("confidence", record.get("confidence", 0.0)), 0.0)
            risk_status = _clean(order.get("risk_status", record.get("risk_status", "risk_review")), "risk_review")
            next_review = _clean(order.get("next_review_time", order.get("estimated_next_review", "next_runtime_cycle")), "next_runtime_cycle")
            # Keep construction explicit so field ordering is stable for tests and dashboard rendering.
            explanation_rows: list[BilingualExplanation] = []
            for field in _FIELDS:
                title_en, title_th, explanation_en, explanation_th = _EXPLANATION_TEXT[field]
                explanation_rows.append(BilingualExplanation(field, title_en, title_th, _value_for(field, order, confidence, risk_status, next_review), explanation_en, explanation_th))
            items.append(ExplainableOrderItem(
                order_id=_clean(order.get("order_id", f"PAPER-{index:04d}"), f"PAPER-{index:04d}"),
                symbol=symbol,
                side=_upper(order.get("side", order.get("action", "BUY")), "BUY"),
                status=_upper(order.get("status", "WAITING"), "WAITING").replace(" ", "_"),
                units=units,
                lot_per_unit=UNIT_LOT,
                total_lot=round(units * UNIT_LOT, 2),
                confidence=round(confidence, 2),
                risk_status=risk_status,
                expected_next_action=_value_for("expected_next_action", order, confidence, risk_status, next_review),
                next_review_time=next_review,
                explanations=tuple(explanation_rows),
            ))
        if broker != VERSION1_BROKER:
            status, reason, ready = "BLOCKED", "version1_xm_only_required", False
        elif symbol != VERSION1_SYMBOL:
            status, reason, ready = "BLOCKED", "version1_gold_only_required", False
        elif live_execution_enabled:
            status, reason, ready = "BLOCKED", "live_execution_disabled_for_explainable_order_center", False
        elif not items:
            status, reason, ready = "WAITING", "explainable_order_center_waiting_for_paper_orders", True
        else:
            status, reason, ready = "READY", "explainable_order_center_ready", True
        return ExplainableOrderCenterReport(status, reason, broker, symbol, False, len(items), _FIELDS, tuple(items), ready)

    def explain_one(self, record: Mapping[str, Any]) -> ExplainableOrderCenterReport:
        return self.evaluate_one(record)
