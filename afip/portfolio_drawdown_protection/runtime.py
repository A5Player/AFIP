"""Milestone N Pack 6: deterministic portfolio drawdown protection.

Research-only portfolio safety gate. It never creates or transmits orders.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping

@dataclass(frozen=True)
class PortfolioDrawdownProtectionReport:
    status: str
    reason: str
    milestone: str
    pack: str
    protection_id: str
    coordination_id: str
    allocation_id: str
    profile_id: str
    market_regime: str
    starting_equity: float
    current_equity: float
    peak_equity: float
    equity_floor: float
    drawdown_amount: float
    drawdown_percent: float
    maximum_drawdown_percent: float
    daily_loss_amount: float
    maximum_daily_loss_amount: float
    consecutive_loss_count: int
    maximum_consecutive_losses: int
    equity_floor_valid: bool
    drawdown_limit_valid: bool
    daily_loss_limit_valid: bool
    consecutive_loss_limit_valid: bool
    exposure_coordination_approved: bool
    independent_position_lifecycles_valid: bool
    protected_runner_exposure_included: bool
    market_regime_before_signal: bool
    forbidden_methods_disabled: bool
    data_quality_certified: bool
    portfolio_drawdown_protection_approved: bool
    portfolio_drawdown_protection_ready: bool
    reduce_new_allocation_required: bool
    preserve_existing_protected_runner: bool
    research_only: bool
    production_knowledge_approved: bool
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

class PortfolioDrawdownProtectionRuntime:
    def evaluate(self, record: Mapping[str, Any]) -> PortfolioDrawdownProtectionReport:
        coordination_id = str(record.get("coordination_id", "")).strip()
        allocation_id = str(record.get("allocation_id", "")).strip()
        profile_id = str(record.get("profile_id", "")).strip()
        regime = str(record.get("market_regime", "")).strip().upper()
        start = max(0.0, self._number(record.get("starting_equity"), 0.0))
        current = max(0.0, self._number(record.get("current_equity"), 0.0))
        peak = max(0.0, self._number(record.get("peak_equity"), 0.0))
        floor = max(0.0, self._number(record.get("equity_floor"), 0.0))
        max_dd = self._number(record.get("maximum_drawdown_percent"), 10.0)
        daily_loss = max(0.0, self._number(record.get("daily_loss_amount"), 0.0))
        max_daily_loss = max(0.0, self._number(record.get("maximum_daily_loss_amount"), 0.0))
        loss_count = max(0, self._integer(record.get("consecutive_loss_count"), 0))
        max_losses = max(0, self._integer(record.get("maximum_consecutive_losses"), 3))
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        base_lot = self._number(record.get("base_lot_per_unit"), 0.01)
        drawdown_amount = max(0.0, peak - current)
        drawdown_percent = (drawdown_amount / peak * 100.0) if peak > 0.0 else 0.0
        coordination_ok = bool(record.get("portfolio_exposure_approved", False)) and bool(record.get("portfolio_exposure_coordination_ready", False))
        lifecycle_ok = bool(record.get("independent_position_lifecycles_valid", False))
        runner_included = bool(record.get("protected_runner_exposure_included", True))
        regime_first = bool(record.get("market_regime_before_signal", True)) and bool(regime)
        forbidden_disabled = all(bool(record.get(key, True)) for key in (
            "traditional_dca_disabled", "averaging_down_disabled", "martingale_disabled", "grid_trading_disabled", "recovery_trading_disabled"))
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))
        equity_floor_valid = current >= floor > 0.0
        dd_valid = 0.0 < max_dd <= 100.0 and drawdown_percent <= max_dd + 1e-12
        daily_valid = max_daily_loss > 0.0 and daily_loss <= max_daily_loss + 1e-12
        streak_valid = max_losses > 0 and loss_count <= max_losses
        checks = (
            (not coordination_id, "exposure_coordination_lineage_missing"),
            (not allocation_id, "capital_allocation_lineage_missing"),
            (not coordination_ok, "portfolio_exposure_not_approved"),
            (not profile_id, "profile_id_missing"),
            (start <= 0.0 or current <= 0.0 or peak <= 0.0, "equity_values_invalid"),
            (peak < current, "peak_equity_below_current_equity"),
            (not equity_floor_valid, "equity_floor_breached"),
            (not dd_valid, "maximum_drawdown_exceeded"),
            (not daily_valid, "maximum_daily_loss_exceeded"),
            (not streak_valid, "maximum_consecutive_losses_exceeded"),
            (not lifecycle_ok, "independent_position_lifecycle_required"),
            (not runner_included, "protected_runner_exposure_excluded"),
            (not regime_first, "market_regime_sequence_invalid"),
            (not forbidden_disabled, "forbidden_trading_method_enabled"),
            (not data_quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (broker != "XM", "broker_policy_violation"),
            (symbol != "GOLD#", "symbol_policy_violation"),
            (abs(base_lot - 0.01) > 1e-12, "base_unit_policy_violation"),
            (str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).upper() != "LOCKED_SIMULATION_ONLY", "execution_lock_invalid"),
            (str(record.get("order_status", "NO_ORDER_SENT")).upper() != "NO_ORDER_SENT", "order_status_invalid"),
            (bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)), "execution_enablement_forbidden"),
            (bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)), "order_transmission_forbidden"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        approved = not blocked
        identity = {"coordination_id": coordination_id, "allocation_id": allocation_id, "profile_id": profile_id, "regime": regime,
                    "equity": [round(start,8), round(current,8), round(peak,8), round(floor,8)],
                    "limits": [round(max_dd,8), round(daily_loss,8), round(max_daily_loss,8), loss_count, max_losses], "blocked": blocked}
        protection_id = "PDP-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if approved:
            reason = "PORTFOLIO_DRAWDOWN_WITHIN_LIMITS"
            en = "Portfolio drawdown, daily loss, loss streak and equity floor remain within certified limits."
            th = "Drawdown, ผลขาดทุนรายวัน, จำนวนขาดทุนต่อเนื่อง และระดับ Equity ของพอร์ตยังอยู่ภายในเพดานที่กำหนด"
            next_en = "Continue research-only portfolio evaluation without enabling execution."
            next_th = "ดำเนินการประเมินพอร์ตในโหมดวิจัยต่อไปโดยไม่เปิดการส่งคำสั่งซื้อขาย"
        else:
            reason = "PORTFOLIO_DRAWDOWN_PROTECTION_BLOCKED"
            en = "New portfolio allocation is blocked by one or more drawdown protection gates."
            th = "การจัดสรรพอร์ตใหม่ถูกระงับโดยเงื่อนไขป้องกัน Drawdown อย่างน้อยหนึ่งรายการ"
            next_en = "Block new allocation, preserve valid protected runners, and review the recorded reasons."
            next_th = "ระงับการจัดสรรใหม่ รักษา Protected Runner ที่ยังถูกต้อง และตรวจสอบเหตุผลที่บันทึกไว้"
        return PortfolioDrawdownProtectionReport(
            status="READY" if approved else "BLOCKED", reason=reason, milestone="N", pack="6",
            protection_id=protection_id, coordination_id=coordination_id, allocation_id=allocation_id,
            profile_id=profile_id, market_regime=regime, starting_equity=round(start,8), current_equity=round(current,8),
            peak_equity=round(peak,8), equity_floor=round(floor,8), drawdown_amount=round(drawdown_amount,8),
            drawdown_percent=round(drawdown_percent,8), maximum_drawdown_percent=round(max_dd,8), daily_loss_amount=round(daily_loss,8),
            maximum_daily_loss_amount=round(max_daily_loss,8), consecutive_loss_count=loss_count, maximum_consecutive_losses=max_losses,
            equity_floor_valid=equity_floor_valid, drawdown_limit_valid=dd_valid, daily_loss_limit_valid=daily_valid,
            consecutive_loss_limit_valid=streak_valid, exposure_coordination_approved=coordination_ok,
            independent_position_lifecycles_valid=lifecycle_ok, protected_runner_exposure_included=runner_included,
            market_regime_before_signal=regime_first, forbidden_methods_disabled=forbidden_disabled,
            data_quality_certified=data_quality, portfolio_drawdown_protection_approved=approved,
            portfolio_drawdown_protection_ready=approved, reduce_new_allocation_required=not approved,
            preserve_existing_protected_runner=True, research_only=True, production_knowledge_approved=False,
            block_reasons=blocked, explanation_reason_en=en, explanation_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            broker="XM", symbol="GOLD#", base_lot_per_unit=0.01, execution_status="LOCKED_SIMULATION_ONLY",
            direct_execution=False, live_execution_enabled=False, order_status="NO_ORDER_SENT",
            broker_request_created=False, order_transmission_attempted=False, trading_logic_changed=False)

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return default
        return result if isfinite(result) else default

    @staticmethod
    def _integer(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
