"""AFIP V1 production activation bridge.

Connects the existing CompleteTradePlan, LotAuthority, TradeLifecycleEngine and
PositionCareSupervisor to the real demo execution gateway.  This module does
not calculate lot sizing.  It accepts the canonical LotAuthority result and
blocks order transmission unless the complete plan is certified.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from afip.complete_trade_plan import (
    CapitalManagementPlan, CompleteTradePlan, CompleteTradePlanCertifier,
    EntryPlan, ExitPlan, FailureRecoveryPlan, MarketSituationPlan,
    PositionCarePlan,
)
from afip.engine.trade_lifecycle_engine import TradeLifecycleEngine
from afip.position_care_runtime import PositionCareSnapshot, PositionCareSupervisor


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(dict(payload), indent=2, sort_keys=True, default=str), encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(dict(payload), sort_keys=True, default=str) + "\n")


class ProductionActivationRuntime:
    """Runtime wiring used by the canonical demo gateway."""

    def __init__(self, *, profile: Any, policy: Any, runtime_root: Path) -> None:
        self.profile = profile
        self.policy = policy
        self.runtime_root = Path(runtime_root)
        self.profile_root = self.runtime_root / "profiles" / str(profile.profile_id).lower()
        self.activation_root = self.profile_root / "production_activation"
        self.plan_root = self.activation_root / "plans"
        self.status_path = self.activation_root / "status.json"
        self.ledger_path = self.activation_root / "activation_ledger.jsonl"
        self.lifecycle = TradeLifecycleEngine()
        self.care = PositionCareSupervisor()

    @staticmethod
    def _identity(*parts: Any) -> str:
        raw = "|".join(str(part) for part in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20].upper()

    def build_and_certify_plan(
        self, *, simulation: Mapping[str, Any], account: Any,
        authority: Any, action: str, confidence: float,
        prepared_requests: list[dict[str, Any]], execution_trace_id: str,
    ) -> tuple[CompleteTradePlan, Any]:
        if not prepared_requests:
            raise ValueError("prepared_requests_required")
        first = prepared_requests[0]
        decision = simulation.get("decision", {}) if isinstance(simulation, Mapping) else {}
        modular = simulation.get("modular_intelligence", {}) if isinstance(simulation, Mapping) else {}
        regime_data = modular.get("market_regime", {}) if isinstance(modular, Mapping) else {}
        pattern_data = modular.get("pattern", modular.get("pattern_intelligence", {})) if isinstance(modular, Mapping) else {}
        symbol = str(first.get("symbol", self.profile.symbol))
        plan_id = f"PLAN-{self._identity(self.profile.profile_id, execution_trace_id, action, confidence)}"
        lots = tuple(float(x) for x in getattr(authority, "approved_lots", ()))
        capacity = int(getattr(authority, "approved_units", len(lots)))
        requested = len(prepared_requests)
        balance = float(_value(account, "balance", 0.0) or 0.0)
        equity = float(_value(account, "equity", balance) or balance)
        margin_free = float(_value(account, "margin_free", _value(account, "margin_free", equity)) or equity)
        stop = float(first.get("sl", 0.0) or 0.0)
        targets = tuple(float(req.get("tp", 0.0) or 0.0) for req in prepared_requests if float(req.get("tp", 0.0) or 0.0) > 0)
        market = MarketSituationPlan(
            regime=str(regime_data.get("regime", regime_data.get("market_regime", decision.get("market_regime", "UNCLASSIFIED")))) or "UNCLASSIFIED",
            pattern_name=str(pattern_data.get("pattern_name", pattern_data.get("pattern", "AFIP_SIGNAL"))) or "AFIP_SIGNAL",
            pattern_family=str(pattern_data.get("family", "AFIP")) or "AFIP",
            structure_state=str(regime_data.get("status", "VALID")) or "VALID",
            volatility_state=str(simulation.get("volatility_state", "ACCEPTABLE")) or "ACCEPTABLE",
            liquidity_state="ACCEPTABLE",
            session=str(simulation.get("session", "AUTO")) or "AUTO",
            news_state=str(simulation.get("news_state", "CHECKED")) or "CHECKED",
            directional_bias=action,
            situation_confidence=float(confidence),
            invalidation_conditions=("hard_stop_reached", "trade_thesis_invalidated"),
        )
        entry_prices = tuple(float(req.get("price", 0.0) or 0.0) for req in prepared_requests)
        entry = EntryPlan(
            direction=action,
            entry_method="AFIP_CANONICAL_GATEWAY",
            entry_zone_low=min(entry_prices), entry_zone_high=max(entry_prices),
            confirmation_conditions=("intelligence_actionable", "risk_approved", "trading_cost_approved"),
            cancellation_conditions=("signal_expired", "spread_blocked", "authority_changed"),
            chase_prohibited=True,
            maximum_signal_age_seconds=max(60, int(getattr(self.policy, "minimum_seconds_between_entries", 900))),
            requested_units=requested, maximum_units=int(getattr(self.policy, "maximum_units", capacity)),
            unit_spacing_points=float(decision.get("minimum_add_spacing_points", 0.0) or 0.0),
            maximum_spread_points=float(simulation.get("trading_cost_intelligence", {}).get("max_spread_points", 1.0) or 1.0),
            maximum_slippage_points=float(first.get("deviation", 20) or 20),
            entry_mode=str(decision.get("entry_mode", "SINGLE_ENTRY")).upper(),
            trade_case_id=str(decision.get("trade_case_id", plan_id)),
            initial_units=1,
            reserved_units=max(0, capacity - requested) if str(decision.get("entry_mode", "SINGLE_ENTRY")).upper() not in {"SINGLE_ENTRY", "NO_ADDITIONAL_ENTRY"} else 0,
            planned_entry_prices=entry_prices,
            minimum_add_spacing_points=float(decision.get("minimum_add_spacing_points", 0.0) or 0.0),
            add_requires_recertification=True,
        )
        capital = CapitalManagementPlan(
            profile_id=str(self.profile.profile_id), base_lot=0.01,
            capital_per_unit=0.0,  # compatibility metadata only; never lot authority
            account_balance=balance, account_equity=equity, free_margin=margin_free,
            current_floating_drawdown_percent=0.0,
            maximum_trade_risk_percent=100.0, maximum_account_drawdown_percent=100.0,
            daily_loss_limit_percent=100.0, weekly_loss_limit_percent=100.0, monthly_loss_limit_percent=100.0,
            capital_capacity_units=capacity, risk_capacity_units=capacity,
            margin_capacity_units=capacity, exposure_capacity_units=capacity,
            correlation_capacity_units=capacity, profile_capacity_units=capacity,
        )
        care = PositionCarePlan(
            holding_thesis="Hold while the certified AFIP trade thesis and protection remain valid.",
            thesis_validation_conditions=("hard_stop_not_reached", "position_identity_matches_plan"),
            thesis_failure_conditions=("hard_stop_reached", "identity_mismatch", "emergency_condition"),
            break_even_trigger="research_ranked_per_profit_role_with_legacy_one_r_fallback",
            trailing_policy="research_ranked_per_profit_role_with_legacy_one_point_five_r_fallback",
            partial_close_policy="disabled_unless_explicit_plan_trigger",
            add_position_policy="reserved_units_only_at_researched_better_price_after_full_recertification",
            maximum_holding_seconds=604800,
            overnight_policy="allowed_by_existing_profile_policy",
            weekend_policy="existing_profile_policy",
            news_management_policy="existing_news_gate",
        )
        exit_plan = ExitPlan(
            initial_stop_price=stop, hard_invalidation_price=stop,
            target_prices=targets or (float(first.get("tp", 0.0) or 0.0),),
            structure_exit_conditions=("trade_thesis_invalidated",),
            time_exit_condition="maximum_holding_seconds",
            thesis_failure_exit="full_close", volatility_exit="position_care_review",
            emergency_exit="full_close", profit_protection_policy="break_even_then_trailing",
            trailing_exit_policy="certified_position_care",
        )
        recovery = FailureRecoveryPlan(
            stale_data_action="block_new_action", mt5_disconnect_action="safe_mode",
            internet_disconnect_action="safe_mode", restart_reconciliation_required=True,
            unknown_order_action="block_and_alert", state_corruption_action="safe_mode",
            spread_anomaly_action="block_new_action", broker_rejection_action="record_and_stop_batch",
            manual_order_guard_action="operator_override", equity_anomaly_action="safe_mode",
            safe_mode_action="no_new_risk", alert_required=True,
        )
        plan = CompleteTradePlan(
            plan_id=plan_id, plan_version="AFIP-V1-PRODUCTION-ACTIVATION",
            symbol=symbol, ranking_id=str(decision.get("ranking_id", execution_trace_id)),
            selected_standard_id=str(decision.get("selected_standard_id", "AFIP_RUNTIME_STANDARD")),
            market=market, entry=entry, capital=capital, care=care, exit=exit_plan, recovery=recovery,
        )
        certification = CompleteTradePlanCertifier().certify(plan)
        order_payload = simulation.get("order", {}) if isinstance(simulation.get("order", {}), Mapping) else {}
        portfolio_payload = order_payload.get("protection_portfolio", {}) if isinstance(order_payload.get("protection_portfolio", {}), Mapping) else {}
        profit_management_plans = [
            dict(value) for value in portfolio_payload.get("unit_plans", ()) if isinstance(value, Mapping)
        ]
        payload = {
            "status": "CERTIFIED" if certification.certified else "BLOCKED",
            "execution_trace_id": execution_trace_id,
            "plan": plan.as_dict(), "certification": certification.as_dict(),
            "lot_authority": authority.as_dict(), "updated_at_utc": _utc(),
            "profit_management_plans": profit_management_plans,
            "profit_management_authority": "RESEARCH_PORTFOLIO_WITH_FAIL_CLOSED_LEGACY_FALLBACK",
        }
        _atomic_json(self.plan_root / f"{plan.plan_id}.json", payload)
        _atomic_json(self.status_path, payload)
        _append_jsonl(self.ledger_path, {"event": "PLAN_CERTIFICATION", **payload})
        return plan, certification

    def register_tickets(self, *, plan: CompleteTradePlan, tickets: list[int], requests: list[dict[str, Any]], execution_trace_id: str,
                         broker_execution_proof: Mapping[str, Any] | None = None) -> None:
        path = self.plan_root / f"{plan.plan_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"plan": plan.as_dict()}
        payload.update({
            "tickets": [int(x) for x in tickets], "requests": requests,
            "execution_trace_id": execution_trace_id, "status": "POSITION_OPENED",
            "broker_execution_proof": dict(broker_execution_proof or {}),
            "updated_at_utc": _utc(),
        })
        plans = [dict(value) for value in payload.get("profit_management_plans", ()) if isinstance(value, Mapping)]
        ticket_profit_plans: dict[str, dict[str, Any]] = {}
        for ticket, request in zip(tickets, requests):
            comment = str(request.get("comment", ""))
            selected = next((value for value in plans if str(value.get("role", "")) in comment), None)
            if selected is not None:
                ticket_profit_plans[str(int(ticket))] = selected
        payload["ticket_profit_plans"] = ticket_profit_plans
        _atomic_json(path, payload)
        _atomic_json(self.status_path, payload)
        _append_jsonl(self.ledger_path, {"event": "POSITION_OPENED", **payload})

    def observe_positions(
        self, *, mt5: Any, positions: list[Any], latest_confidence: float = 50.0,
        current_intelligence: Mapping[str, Any] | None = None,
        execution_trace_id: str = "",
    ) -> dict[str, Any]:
        """Evaluate lifecycle and position care for real MT5 positions.

        Break-even and trailing modifications are sent only on DEMO accounts and
        only when the original certified plan can be reconciled by ticket.
        """
        records: list[dict[str, Any]] = []
        intelligence_context = self._position_intelligence_context(current_intelligence or {})
        for position in positions:
            ticket = int(_value(position, "ticket", 0) or 0)
            plan_payload = None
            for plan_file in self.plan_root.glob("PLAN-*.json"):
                try:
                    candidate = json.loads(plan_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if ticket in [int(x) for x in candidate.get("tickets", [])]:
                    plan_payload = candidate
                    break
            if not plan_payload:
                records.append({"ticket": ticket, "status": "UNRECONCILED", "reason": "certified_plan_not_found"})
                continue
            plan = self._plan_from_dict(plan_payload["plan"])
            current = float(_value(position, "price_current", 0.0) or 0.0)
            opened = float(_value(position, "price_open", 0.0) or 0.0)
            sl = float(_value(position, "sl", 0.0) or 0.0)
            tp = float(_value(position, "tp", 0.0) or 0.0)
            point = float(_value(mt5.symbol_info(self.profile.symbol), "point", 0.01) or 0.01)
            buy = int(_value(position, "type", 0) or 0) == int(getattr(mt5, "POSITION_TYPE_BUY", 0))
            favorable = max(0.0, (current-opened if buy else opened-current) / point)
            adverse = max(0.0, (opened-current if buy else current-opened) / point)
            risk_points = abs(opened - float(plan.exit.initial_stop_price)) / point if point > 0 else 0.0
            ticket_profit_plan = _value(plan_payload.get("ticket_profit_plans", {}), str(ticket), {})
            if not isinstance(ticket_profit_plan, Mapping):
                ticket_profit_plan = {}
            break_even_trigger_r = float(ticket_profit_plan.get("break_even_trigger_r", 1.0) or 1.0)
            trailing_start_r = float(ticket_profit_plan.get("trailing_start_r", 1.5) or 1.5)
            maximum_giveback_r = float(ticket_profit_plan.get("maximum_giveback_r", 0.0) or 0.0)
            lifecycle = self.lifecycle.evaluate({
                "floating_profit": float(_value(position, "profit", 0.0) or 0.0),
                "peak_profit": max(0.0, float(_value(position, "profit", 0.0) or 0.0)),
                "position_confidence": latest_confidence,
            })
            snapshot = PositionCareSnapshot(
                snapshot_id=f"PCS-{self._identity(ticket, current, sl, tp)}",
                plan_id=plan.plan_id, profile_id=str(self.profile.profile_id), symbol=self.profile.symbol,
                ticket=str(ticket), direction="BUY" if buy else "SELL", entry_price=opened,
                current_price=current, initial_stop_price=float(plan.exit.initial_stop_price),
                current_stop_price=sl, current_take_profit_price=tp,
                volume_lots=float(_value(position, "volume", 0.0) or 0.0),
                unrealized_profit=float(_value(position, "profit", 0.0) or 0.0),
                favorable_points=favorable, adverse_points=adverse,
                holding_seconds=max(0, int(datetime.now(timezone.utc).timestamp()) - int(_value(position, "time", 0) or 0)),
                market_regime_valid=bool(intelligence_context["market_regime_valid"]),
                thesis_valid=self._thesis_valid_for_position(
                    position_direction="BUY" if buy else "SELL", context=intelligence_context
                ),
                structure_valid=self._module_supports_position(
                    "MarketStructureIntelligence", "BUY" if buy else "SELL", intelligence_context
                ),
                volatility_acceptable=bool(intelligence_context["volatility_acceptable"]),
                liquidity_acceptable=bool(intelligence_context["liquidity_acceptable"]),
                market_data_fresh=bool(intelligence_context["market_data_fresh"]),
                connection_ready=True, account_state_reconciled=True,
                break_even_triggered=risk_points > 0 and favorable >= risk_points * break_even_trigger_r,
                trailing_triggered=risk_points > 0 and favorable >= risk_points * trailing_start_r,
                partial_close_triggered=False,
                target_reached=(tp > 0 and ((buy and current >= tp) or ((not buy) and current <= tp))),
                hard_invalidation_reached=(sl > 0 and ((buy and current <= sl) or ((not buy) and current >= sl))),
                emergency_condition_active=False, observed_at=_utc(),
            )
            care = self.care.evaluate(plan=plan, snapshot=snapshot)
            action_result = self._execute_position_action(mt5=mt5, position=position, decision=care)
            record = {
                "ticket": ticket,
                "execution_trace_id": execution_trace_id,
                "lifecycle": lifecycle,
                "position_snapshot": snapshot.as_dict(),
                "position_care": care.as_dict(),
                "intelligence_context": intelligence_context,
                "mt5_action": action_result,
                "profit_management_plan": dict(ticket_profit_plan),
                "profit_management_thresholds": {
                    "break_even_trigger_r": break_even_trigger_r,
                    "trailing_start_r": trailing_start_r,
                    "maximum_giveback_r": maximum_giveback_r,
                    "automatic_full_close_on_giveback": False,
                },
                "updated_at_utc": _utc(),
            }
            records.append(record)
            _append_jsonl(self.ledger_path, {"event": "POSITION_CARE", **record})
        closed_records = self._reconcile_closed_positions(mt5=mt5, open_tickets={int(_value(p, "ticket", 0) or 0) for p in positions})
        result = {
            "status": "ACTIVE",
            "position_management_policy": {
                # Compatibility evidence for the retired same-batch rule:
                # "pyramiding": "NO_ADDITIONAL_UNITS_OUTSIDE_ORIGINAL_CERTIFIED_PLAN"
                "holding": "INTELLIGENCE_AND_CERTIFIED_PLAN",
                "break_even": "DEMO_ONLY_RESEARCH_RANKED_PER_ROLE_WITH_CERTIFIED_SLTP",
                "trailing": "DEMO_ONLY_RESEARCH_RANKED_PER_ROLE_WITH_CERTIFIED_SLTP",
                "single_001_profit_diversification": "TEMPORAL_TP_BREAK_EVEN_TRAILING_AND_RESEARCH_OBSERVATION_NO_PARTIAL_VOLUME",
                "partial_close": "DISABLED_UNTIL_EXPLICIT_CERTIFIED_TRIGGER",
                "scale_out": "DISABLED_UNTIL_EXPLICIT_CERTIFIED_TRIGGER",
                "pyramiding": "ONE_LEG_PER_CYCLE_RESERVED_UNITS_REQUIRE_RESEARCHED_BETTER_PRICE_AND_FULL_RECERTIFICATION",
                "automatic_full_close": "NOT_ENABLED_BY_THIS_BRIDGE",
            },
            "positions_evaluated": len(records),
            "records": records,
            "closed_positions_recorded": len(closed_records),
            "closed_records": closed_records,
            "updated_at_utc": _utc(),
        }
        _atomic_json(self.activation_root / "position_care_status.json", result)
        return result

    def _reconcile_closed_positions(self, *, mt5: Any, open_tickets: set[int]) -> list[dict[str, Any]]:
        """Record broker-closed certified tickets for research only.

        This method never sends an order. It reads MT5 deal history when the
        adapter exposes ``history_deals_get`` and emits an append-only closure
        event once per certified ticket.
        """
        history_get = getattr(mt5, "history_deals_get", None)
        if not callable(history_get):
            return []
        now = datetime.now(timezone.utc)
        closed: list[dict[str, Any]] = []
        for plan_file in self.plan_root.glob("PLAN-*.json"):
            try:
                plan_payload = json.loads(plan_file.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            recorded = {int(x) for x in plan_payload.get("research_closed_tickets", [])}
            tickets = {int(x) for x in plan_payload.get("tickets", [])}
            for ticket in sorted(tickets - open_tickets - recorded):
                try:
                    deals = history_get(position=ticket) or ()
                except TypeError:
                    deals = history_get(now.replace(year=max(1970, now.year - 1)), now) or ()
                    deals = [d for d in deals if int(_value(d, "position_id", 0) or 0) == ticket]
                if not deals:
                    continue
                realized = sum(float(_value(d, "profit", 0.0) or 0.0) + float(_value(d, "swap", 0.0) or 0.0) + float(_value(d, "commission", 0.0) or 0.0) for d in deals)
                latest = max(deals, key=lambda d: int(_value(d, "time", 0) or 0))
                payload = {
                    "event": "POSITION_CLOSED",
                    "ticket": ticket,
                    "plan_id": str(plan_payload.get("plan", {}).get("plan_id", plan_file.stem)),
                    "profile_id": str(self.profile.profile_id),
                    "symbol": str(self.profile.symbol),
                    "realized_profit": realized,
                    "exit_price": float(_value(latest, "price", 0.0) or 0.0),
                    "exit_reason": "BROKER_HISTORY_RECONCILIATION",
                    "observed_at_utc": _utc(),
                    "research_only": True,
                    "affects_trading": False,
                }
                _append_jsonl(self.ledger_path, payload)
                closed.append(payload)
                recorded.add(ticket)
            if recorded:
                plan_payload["research_closed_tickets"] = sorted(recorded)
                plan_payload["updated_at_utc"] = _utc()
                _atomic_json(plan_file, plan_payload)
        return closed


    @staticmethod
    def _position_intelligence_context(simulation: Mapping[str, Any]) -> dict[str, Any]:
        decision = simulation.get("decision", {}) if isinstance(simulation, Mapping) else {}
        explain = decision.get("explain", ()) if isinstance(decision, Mapping) else ()
        modules: dict[str, dict[str, Any]] = {}
        if isinstance(explain, (list, tuple)):
            for row in explain:
                if isinstance(row, Mapping):
                    modules[str(row.get("name", "UNKNOWN"))] = dict(row)
        blocking = decision.get("blocking_intelligence", ()) if isinstance(decision, Mapping) else ()
        data_status = str(simulation.get("data_status", "UNKNOWN")).upper()
        data_source = str(simulation.get("data_source", "UNKNOWN")).upper()
        def acceptable(name: str) -> bool:
            row = modules.get(name, {})
            return str(row.get("status", "UNKNOWN")).upper() not in {"BLOCKED", "FAIL", "ERROR"}
        return {
            "decision_action": str(decision.get("action", "WAIT")).upper(),
            "decision_confidence": float(decision.get("confidence", 0.0) or 0.0),
            "decision_reason": str(decision.get("reason", "not_evaluated")),
            "conflict_resolution_reason": str(decision.get("conflict_resolution_reason", "not_evaluated")),
            "selected_scenario": str(decision.get("selected_scenario", "NOT_EVALUATED")),
            "market_regime_valid": acceptable("MarketRegimeIntelligence") and not bool(blocking),
            "volatility_acceptable": acceptable("VolatilityRiskIntelligence"),
            "liquidity_acceptable": acceptable("LiquidityIntelligence"),
            "market_data_fresh": not any(token in data_status or token in data_source for token in ("FALLBACK", "STALE", "ERROR")),
            "modules": modules,
        }

    @staticmethod
    def _module_supports_position(name: str, position_direction: str, context: Mapping[str, Any]) -> bool:
        row = context.get("modules", {}).get(name, {}) if isinstance(context.get("modules"), Mapping) else {}
        status = str(row.get("status", "UNKNOWN")).upper()
        direction = str(row.get("direction", "FLAT")).upper()
        if status in {"BLOCKED", "FAIL", "ERROR"}:
            return False
        return direction not in {"BUY", "SELL"} or direction == position_direction.upper()

    @staticmethod
    def _thesis_valid_for_position(*, position_direction: str, context: Mapping[str, Any]) -> bool:
        action = str(context.get("decision_action", "WAIT")).upper()
        confidence = float(context.get("decision_confidence", 0.0) or 0.0)
        if action in {"BUY", "SELL"} and action != position_direction.upper() and confidence >= 60.0:
            return False
        return True

    def _execute_position_action(self, *, mt5: Any, position: Any, decision: Any) -> dict[str, Any]:
        action = str(decision.recommended_action)
        ticket = int(_value(position, "ticket", 0) or 0)
        if action not in {"RECOMMEND_BREAK_EVEN_UPDATE", "RECOMMEND_TRAILING_STOP_UPDATE"}:
            return {
                "status": "NO_ACTION", "action": action,
                "order_check_called": False, "order_send_called": False,
                "policy": "HOLD_OR_RECOMMENDATION_ONLY",
            }
        if not self._demo_account_verified(mt5):
            return {
                "status": "BLOCKED", "action": action,
                "order_check_called": False, "order_send_called": False,
                "reason": "demo_account_not_verified",
            }
        proposed = float(decision.proposed_stop_price)
        valid, reason = self._validate_stop_improvement(mt5=mt5, position=position, proposed_stop=proposed)
        if not valid:
            return {
                "status": "NO_CHANGE" if reason == "stop_not_improved" else "BLOCKED",
                "action": action, "order_check_called": False, "order_send_called": False,
                "reason": reason, "proposed_stop_price": proposed,
            }
        request = {
            "action": getattr(mt5, "TRADE_ACTION_SLTP"), "position": ticket,
            "symbol": self.profile.symbol, "sl": proposed,
            "tp": float(_value(position, "tp", 0.0) or 0.0), "magic": int(self.policy.magic),
            "comment": f"AFIP {self.profile.profile_id} POSITION_CARE",
        }
        check = mt5.order_check(request)
        if check is None or int(_value(check, "retcode", -1)) != 0:
            return {"status": "BLOCKED", "action": action, "order_check_called": True, "order_send_called": False, "reason": str(_value(check, "comment", mt5.last_error()))}
        result = mt5.order_send(request)
        success = result is not None and int(_value(result, "retcode", -1)) in {int(getattr(mt5, n)) for n in ("TRADE_RETCODE_DONE", "TRADE_RETCODE_PLACED", "TRADE_RETCODE_DONE_PARTIAL") if hasattr(mt5, n)}
        return {"status": "EXECUTED" if success else "ERROR", "action": action, "order_check_called": True, "order_send_called": True, "retcode": int(_value(result, "retcode", -1)), "comment": str(_value(result, "comment", "")), "proposed_stop_price": proposed}

    @staticmethod
    def _demo_account_verified(mt5: Any) -> bool:
        account_info = getattr(mt5, "account_info", None)
        if not callable(account_info):
            return False
        account = account_info()
        if account is None:
            return False
        trade_mode = _value(account, "trade_mode", None)
        demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", None)
        return demo_mode is not None and trade_mode is not None and int(trade_mode) == int(demo_mode)

    def _validate_stop_improvement(self, *, mt5: Any, position: Any, proposed_stop: float) -> tuple[bool, str]:
        if proposed_stop <= 0:
            return False, "proposed_stop_missing"
        info = mt5.symbol_info(self.profile.symbol)
        point = float(_value(info, "point", 0.0) or 0.0)
        if point <= 0:
            return False, "symbol_point_unavailable"
        current_price = float(_value(position, "price_current", 0.0) or 0.0)
        current_stop = float(_value(position, "sl", 0.0) or 0.0)
        buy = int(_value(position, "type", 0) or 0) == int(getattr(mt5, "POSITION_TYPE_BUY", 0))
        minimum_change = point * 0.5
        if buy:
            if current_stop > 0 and proposed_stop <= current_stop + minimum_change:
                return False, "stop_not_improved"
            if proposed_stop >= current_price - point:
                return False, "buy_stop_crosses_market"
        else:
            if current_stop > 0 and proposed_stop >= current_stop - minimum_change:
                return False, "stop_not_improved"
            if proposed_stop <= current_price + point:
                return False, "sell_stop_crosses_market"
        return True, "stop_improvement_certified"

    @staticmethod
    def _plan_from_dict(raw: Mapping[str, Any]) -> CompleteTradePlan:
        return CompleteTradePlan(
            plan_id=raw["plan_id"], plan_version=raw["plan_version"], symbol=raw["symbol"],
            ranking_id=raw["ranking_id"], selected_standard_id=raw["selected_standard_id"],
            market=MarketSituationPlan(**raw["market"]), entry=EntryPlan(**raw["entry"]),
            capital=CapitalManagementPlan(**raw["capital"]), care=PositionCarePlan(**raw["care"]),
            exit=ExitPlan(**raw["exit"]), recovery=FailureRecoveryPlan(**raw["recovery"]),
            created_at=raw.get("created_at", _utc()),
        )
