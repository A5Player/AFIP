"""Milestone N Pack 3: deterministic, research-only portfolio risk engine."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class PortfolioRiskEngineReport:
    status: str
    reason: str
    milestone: str
    pack: str
    risk_evaluation_id: str
    foundation_id: str
    sizing_id: str
    profile_id: str
    market_regime: str
    equity: float
    free_margin: float
    current_open_risk_amount: float
    proposed_risk_amount: float
    total_portfolio_risk_amount: float
    total_portfolio_risk_percent: float
    maximum_portfolio_risk_percent: float
    current_drawdown_percent: float
    maximum_drawdown_percent: float
    margin_level_percent: float
    minimum_margin_level_percent: float
    current_units: int
    proposed_units: int
    total_units: int
    maximum_portfolio_units: int
    position_count: int
    protected_runner_count: int
    risk_budget_valid: bool
    drawdown_valid: bool
    margin_level_valid: bool
    exposure_valid: bool
    position_lineage_valid: bool
    market_regime_before_signal: bool
    independent_position_lifecycle_valid: bool
    protected_runner_exposure_included: bool
    forbidden_methods_disabled: bool
    portfolio_risk_approved: bool
    portfolio_risk_engine_ready: bool
    research_only: bool
    production_knowledge_approved: bool
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

class PortfolioRiskEngineRuntime:
    """Aggregates current and proposed risk without execution authority."""

    def evaluate(self, record: Mapping[str, Any], positions: Iterable[Mapping[str, Any]] = ()) -> PortfolioRiskEngineReport:
        foundation_id = str(record.get("foundation_id", "")).strip()
        sizing_id = str(record.get("sizing_id", "")).strip()
        profile_id = str(record.get("profile_id", "")).strip()
        regime = str(record.get("market_regime", "")).strip().upper()
        equity = self._number(record.get("equity"), 0.0)
        free_margin = self._number(record.get("free_margin"), 0.0)
        proposed_risk = max(0.0, self._number(record.get("proposed_risk_amount"), 0.0))
        proposed_units = max(0, self._integer(record.get("proposed_units"), 0))
        max_risk_pct = self._number(record.get("maximum_portfolio_risk_percent"), 3.0)
        drawdown_pct = max(0.0, self._number(record.get("current_drawdown_percent"), 0.0))
        max_drawdown_pct = self._number(record.get("maximum_drawdown_percent"), 10.0)
        margin_level = self._number(record.get("margin_level_percent"), 0.0)
        min_margin_level = self._number(record.get("minimum_margin_level_percent"), 300.0)
        max_units = self._integer(record.get("maximum_portfolio_units"), 3)
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"

        normalized=[]; ids=[]; current_risk=0.0; current_units=0; runners=0
        lineage_valid=True; lifecycle_valid=True
        for raw in positions:
            p=dict(raw); pid=str(p.get("position_id", "")).strip(); ids.append(pid)
            risk=max(0.0, self._number(p.get("risk_amount"), 0.0)); units=max(0,self._integer(p.get("units"),0))
            current_risk += risk; current_units += units; runners += int(bool(p.get("protected_runner", False)))
            lineage_valid = lineage_valid and bool(pid) and bool(str(p.get("trade_plan_id", "")).strip())
            lifecycle_valid = lifecycle_valid and bool(p.get("independent_position_lifecycle", True))
            normalized.append({"position_id":pid,"trade_plan_id":str(p.get("trade_plan_id", "")),"risk":round(risk,8),"units":units,"runner":bool(p.get("protected_runner",False))})
        lineage_valid = lineage_valid and len(ids)==len(set(ids))
        total_risk=current_risk+proposed_risk
        risk_pct=(total_risk/equity*100.0) if equity>0 else 0.0
        total_units=current_units+proposed_units
        risk_valid=equity>0 and 0<max_risk_pct<=10 and risk_pct<=max_risk_pct
        drawdown_valid=0<=drawdown_pct<=max_drawdown_pct and 0<max_drawdown_pct<=50
        margin_valid=free_margin>=0 and margin_level>=min_margin_level and min_margin_level>0
        exposure_valid=0<=total_units<=max_units and 0<=max_units<=3
        regime_first=bool(record.get("market_regime_before_signal",True)) and bool(regime)
        runner_included=bool(record.get("protected_runner_exposure_included",True))
        forbidden_disabled=all(bool(record.get(k,True)) for k in (
            "traditional_dca_disabled","averaging_down_disabled","martingale_disabled","grid_trading_disabled","recovery_trading_disabled"))
        foundation_ready=bool(record.get("portfolio_intelligence_foundation_ready",False))
        sizing_ready=bool(record.get("adaptive_position_sizing_ready",False))
        data_quality=bool(record.get("data_quality_certified",False))
        future_safe=not bool(record.get("future_leakage_detected",False))

        blocked=[]
        checks=[
            (not foundation_id,"portfolio_foundation_lineage_missing"),(not foundation_ready,"portfolio_foundation_not_ready"),
            (not sizing_id,"adaptive_sizing_lineage_missing"),(not sizing_ready,"adaptive_position_sizing_not_ready"),
            (not profile_id,"profile_id_missing"),(not risk_valid,"portfolio_risk_budget_exceeded"),
            (not drawdown_valid,"drawdown_limit_exceeded"),(not margin_valid,"margin_level_below_minimum"),
            (not exposure_valid,"portfolio_exposure_limit_exceeded"),(not lineage_valid,"position_lineage_invalid"),
            (not lifecycle_valid,"independent_position_lifecycle_required"),(not regime_first,"market_regime_sequence_invalid"),
            (not runner_included,"protected_runner_exposure_missing"),(not forbidden_disabled,"forbidden_trading_method_enabled"),
            (not data_quality,"data_quality_not_certified"),(not future_safe,"future_leakage_detected"),
            (broker!="XM","broker_policy_violation"),(symbol!="GOLD#","symbol_policy_violation"),
            (str(record.get("execution_status","LOCKED_SIMULATION_ONLY")).upper()!="LOCKED_SIMULATION_ONLY","execution_lock_invalid"),
            (str(record.get("order_status","NO_ORDER_SENT")).upper()!="NO_ORDER_SENT","order_status_invalid"),
            (bool(record.get("direct_execution",False)) or bool(record.get("live_execution_enabled",False)),"execution_enablement_forbidden"),
            (bool(record.get("broker_request_created",False)) or bool(record.get("order_transmission_attempted",False)),"order_transmission_forbidden")]
        blocked=[reason for condition,reason in checks if condition]
        approved=not blocked
        identity={"foundation_id":foundation_id,"sizing_id":sizing_id,"profile_id":profile_id,"regime":regime,
                  "equity":round(equity,8),"free_margin":round(free_margin,8),"current_risk":round(current_risk,8),
                  "proposed_risk":round(proposed_risk,8),"limits":[round(max_risk_pct,8),round(max_drawdown_pct,8),round(min_margin_level,8),max_units],
                  "positions":sorted(normalized,key=lambda x:(x["position_id"],x["trade_plan_id"])),"blocked":sorted(set(blocked))}
        rid="PRE-"+sha256(json.dumps(identity,sort_keys=True,separators=(",",":" )).encode()).hexdigest()[:16].upper()
        return PortfolioRiskEngineReport(
            status="READY" if approved else "BLOCKED", reason="Portfolio risk evidence is approved under research-only authority." if approved else "Portfolio risk is blocked by budget, drawdown, margin, exposure, lineage, policy or safety controls.",
            milestone="N",pack="3",risk_evaluation_id=rid,foundation_id=foundation_id,sizing_id=sizing_id,profile_id=profile_id,market_regime=regime,
            equity=round(equity,8),free_margin=round(free_margin,8),current_open_risk_amount=round(current_risk,8),proposed_risk_amount=round(proposed_risk,8),
            total_portfolio_risk_amount=round(total_risk,8),total_portfolio_risk_percent=round(risk_pct,8),maximum_portfolio_risk_percent=round(max_risk_pct,8),
            current_drawdown_percent=round(drawdown_pct,8),maximum_drawdown_percent=round(max_drawdown_pct,8),margin_level_percent=round(margin_level,8),minimum_margin_level_percent=round(min_margin_level,8),
            current_units=current_units,proposed_units=proposed_units,total_units=total_units,maximum_portfolio_units=max_units,position_count=len(normalized),protected_runner_count=runners,
            risk_budget_valid=risk_valid,drawdown_valid=drawdown_valid,margin_level_valid=margin_valid,exposure_valid=exposure_valid,position_lineage_valid=lineage_valid,
            market_regime_before_signal=regime_first,independent_position_lifecycle_valid=lifecycle_valid,protected_runner_exposure_included=runner_included,
            forbidden_methods_disabled=forbidden_disabled,portfolio_risk_approved=approved,portfolio_risk_engine_ready=approved,research_only=True,production_knowledge_approved=False,
            block_reasons=tuple(sorted(set(blocked))),
            explanation_reason_en="Aggregates current and proposed position risk before any execution decision while preserving independent position lifecycles and protected-runner exposure." if approved else "No portfolio risk approval is issued until every risk and safety gate passes.",
            explanation_reason_th="รวมความเสี่ยงของ Position ปัจจุบันและที่เสนอ ก่อนการตัดสินใจด้าน Execution โดยรักษาวงจรชีวิต Position แยกอิสระและรวม Exposure ของ Protected Runner" if approved else "ไม่อนุมัติความเสี่ยง Portfolio จนกว่าเกณฑ์ Risk และ Safety จะผ่านครบ",
            expected_next_action_en="Continue to Milestone N Pack 4 — Capital Allocation." if approved else "Correct blocked portfolio risk evidence and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone N Pack 4 — Capital Allocation" if approved else "แก้หลักฐาน Portfolio Risk ที่ถูกบล็อกแล้วประเมินใหม่",broker=broker,symbol=symbol)

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            n=float(value); return n if isfinite(n) else default
        except (TypeError,ValueError): return default
    @staticmethod
    def _integer(value: Any, default: int) -> int:
        try: return int(value)
        except (TypeError,ValueError): return default
