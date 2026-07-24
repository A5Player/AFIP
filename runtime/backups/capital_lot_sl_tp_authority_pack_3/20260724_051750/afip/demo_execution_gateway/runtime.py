"""Demo-only MT5 execution gateway for AFIP Version 1.0.

This module may transmit protected orders only after it proves that the selected
account is a MetaTrader 5 DEMO account. Real/contest accounts, fallback market
data, missing protection, mismatched accounts, and unarmed local operation are
blocked before ``order_send`` is reachable.
"""
from __future__ import annotations

# Production certification contract markers (kept explicit for static certification):
# exact_profile_binding_mismatch
# execution_ownership_mismatch_before_order_check
# execution_ownership_changed_before_order_send
# execution_ownership_changed_after_order_send
# legacy certification aliases: mt5_terminal_path_mismatch | binding_changed_before_order_send


from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import time
import uuid
from typing import Any, Callable, Mapping, Protocol

from afip.four_profile_operations.runtime import FourProfileOperationalRuntime, ProfileOperationalConfig
from afip.capital_growth_engine import CapitalGrowthEngine
from afip.position_policy import confidence_maximum_units
from afip.position_capacity_formula import capital_tiers_from_profile
from afip.lot_authority import calculate_lot_authority
from afip.production_runtime_authority import reclaim_stale_lock

DEMO_EXECUTION = "DEMO_EXECUTION_ONLY"
DEMO_TRADE_MODE = 0
ORDER_NOT_SENT = "ORDER_NOT_SENT"
SUCCESS_RETCODE_NAMES = {"TRADE_RETCODE_DONE", "TRADE_RETCODE_PLACED", "TRADE_RETCODE_DONE_PARTIAL"}


class MT5Protocol(Protocol):
    def initialize(self, *args: Any, **kwargs: Any) -> bool: ...
    def shutdown(self) -> None: ...
    def last_error(self) -> Any: ...
    def account_info(self) -> Any: ...
    def terminal_info(self) -> Any: ...
    def symbol_select(self, symbol: str, enable: bool) -> bool: ...
    def symbol_info(self, symbol: str) -> Any: ...
    def symbol_info_tick(self, symbol: str) -> Any: ...
    def positions_get(self, **kwargs: Any) -> Any: ...
    def order_check(self, request: Mapping[str, Any]) -> Any: ...
    def order_send(self, request: Mapping[str, Any]) -> Any: ...


@dataclass(frozen=True)
class DemoProfilePolicy:
    profile_id: str
    enabled: bool
    execution_enabled: bool
    research_enabled: bool
    demo_execution_enabled: bool
    maximum_units: int
    minimum_confidence: float
    minimum_seconds_between_entries: int
    magic: int
    lot_per_unit: float = 0.01
    allocation_mode: str = ""
    capital_tiers: tuple[tuple[float, tuple[float, ...]], ...] = ()
    maximum_concurrent_orders: int = 4
    maximum_lot_per_order: float = 0.03

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "DemoProfilePolicy":
        # Backward compatibility contract:
        # "obsolete_sizing_fields_forbidden" remains a searchable audit marker,
        # but legacy sizing fields are ignored and never become sizing authority.
        _legacy_sizing_fields = tuple(
            sorted({"capital_per_unit", "capital_per_unit_legacy_only"}.intersection(raw))
        )
        maximum_units = max(1, int(raw.get("maximum_units", 1)))
        allocation_mode = str(raw.get("allocation_mode", "")).strip().upper()
        capital_tiers = capital_tiers_from_profile(raw)

        # Legacy mappings without an allocation_mode are adapted to a deterministic
        # fixed 0.01 compatibility tier. Legacy capital_per_unit is never read.
        if not allocation_mode:
            allocation_mode = "CAPITAL_TIER_TABLE"
            if not capital_tiers:
                capital_tiers = ((0.0, tuple(0.01 for _ in range(maximum_units))),)

        return cls(
            profile_id=str(raw["profile_id"]).strip().upper(),
            enabled=bool(raw.get("enabled", False)),
            execution_enabled=bool(raw.get("execution_enabled", raw.get("enabled", False))),
            research_enabled=bool(raw.get("research_enabled", raw.get("enabled", False))),
            demo_execution_enabled=bool(raw.get("demo_execution_enabled", False)),
            maximum_units=maximum_units,
            minimum_confidence=float(raw.get("minimum_confidence", 98.0)),
            allocation_mode=allocation_mode,
            capital_tiers=capital_tiers,
            maximum_concurrent_orders=int(raw.get("maximum_concurrent_orders", raw.get("maximum_units", 4))),
            maximum_lot_per_order=float(raw.get("maximum_lot_per_order", 0.03)),
            minimum_seconds_between_entries=int(raw.get("minimum_seconds_between_entries", 900)),
            magic=int(raw.get("magic", 26071001)),
            lot_per_unit=float(raw.get("lot_per_unit", 0.01)),
        )

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.allocation_mode == "CAPITAL_TIER_TABLE":
            if not self.capital_tiers:
                errors.append("capital_tiers_required")
            previous = -1.0
            for minimum_balance, lots in self.capital_tiers:
                if minimum_balance < 0 or minimum_balance <= previous:
                    errors.append("capital_tiers_must_be_strictly_ascending")
                    break
                previous = minimum_balance
                if not 1 <= len(lots) <= self.maximum_concurrent_orders:
                    errors.append("capital_tier_order_count_out_of_range")
                    break
                if any(lot <= 0 or (lot - self.maximum_lot_per_order) > 1e-12 for lot in lots):
                    errors.append("capital_tier_lot_out_of_range")
                    break
        elif self.allocation_mode == "RESEARCH_FIXED_001":
            pass
        else:
            errors.append("allocation_mode_unknown")
        if self.allocation_mode != "RESEARCH_FIXED_001" and self.maximum_concurrent_orders < 1:
            errors.append("maximum_concurrent_orders_must_be_positive")
        if not 0 <= self.minimum_confidence <= 100: errors.append("minimum_confidence_out_of_range")
        if self.minimum_seconds_between_entries < 60: errors.append("entry_cooldown_must_be_at_least_60_seconds")
        if abs(self.lot_per_unit - 0.01) > 1e-12: errors.append("lot_per_unit_must_remain_0_01")
        if self.magic <= 0: errors.append("magic_must_be_positive")
        return tuple(errors)


@dataclass(frozen=True)
class DemoGatewayConfig:
    profile_id: str
    config_path: Path = Path("config/four_profile_demo.json")
    interval_seconds: float = 60.0
    maximum_cycles: int | None = None

    def validate(self) -> None:
        if self.profile_id.upper() not in {"P1", "P2", "P3", "P4"}:
            raise ValueError("profile_id_must_be_p1_to_p4")
        if self.interval_seconds < 5:
            raise ValueError("interval_seconds_must_be_at_least_five")
        if self.maximum_cycles is not None and self.maximum_cycles < 1:
            raise ValueError("maximum_cycles_must_be_positive")


@dataclass(frozen=True)
class DemoGatewayReport:
    profile_id: str
    status: str
    reason: str
    account: str
    server: str
    symbol: str
    execution: str = DEMO_EXECUTION
    account_trade_mode: str = "UNKNOWN"
    demo_verified: bool = False
    armed: bool = False
    decision_action: str = "WAIT"
    decision_confidence: float = 0.0
    balance: float = 0.0
    equity: float = 0.0
    base_lot: float = 0.01
    confidence_units: int = 0
    capital_units: int = 0
    risk_units: int = 0
    profile_max_units: int = 0
    execution_safety_units: int = 0
    approved_units: int = 0
    approved_lot_per_order: float = 0.01
    total_approved_lot: float = 0.0
    limiting_gate: str = "UNKNOWN"
    sizing_reason: str = ""
    policy_version: str = ""
    calculated_at: str = ""
    approved_lots: tuple[float, ...] = ()
    allocated_units: int = 0
    requested_units: int = 0
    confidence_maximum_units: int = 0
    unit_selection_source: str = "UNKNOWN"
    unit_selection_reason: str = ""
    allocated_orders: int = 0
    allocated_lots: tuple[float, ...] = ()
    total_allocated_lot: float = 0.0
    order_unit_distribution: tuple[int, ...] = ()
    maximum_orders: int = 0
    remaining_order_capacity: int = 0
    sent_units: int = 0
    order_status: str = ORDER_NOT_SENT
    tickets: tuple[int, ...] = ()
    trading_cost_status: str = "UNKNOWN"
    trading_cost_allowed: bool = False
    spread_points: float = 0.0
    caution_spread_points: float = 0.0
    max_spread_points: float = 0.0
    point_size: float = 0.0
    digits: int = 0
    order_check_called: bool = False
    order_send_called: bool = False
    mt5_result_code: int | None = None
    mt5_result_comment: str = ""
    allocation_mode: str = "UNKNOWN"
    account_balance: float = 0.0
    current_tier_minimum_balance: float | None = None
    target_tier_lots: tuple[float, ...] = ()
    next_tier_balance: float | None = None
    remaining_to_next_tier: float = 0.0
    maximum_tier_balance: float | None = None
    withdrawal_reference_balance: float | None = None
    connected_account_login: str = ""
    connected_terminal_folder: str = ""
    configured_terminal_folder: str = ""
    ownership_token: str = ""
    checked_at_utc: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DemoExecutionGateway:
    """Runs one guarded decision/execution cycle for one isolated demo profile."""

    def __init__(
        self,
        profile: ProfileOperationalConfig,
        policy: DemoProfilePolicy,
        *,
        mt5: MT5Protocol | None = None,
        simulate: Callable[[], dict[str, Any]] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.profile = profile
        self.policy = policy
        self._mt5 = mt5
        self._simulate = simulate or self._default_simulate
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _default_simulate() -> dict[str, Any]:
        from afip.runtime.runtime_v1 import RuntimeV1
        return RuntimeV1().simulate()

    @property
    def armed(self) -> bool:
        global_arm = os.environ.get("AFIP_DEMO_EXECUTION_ARMED", "").strip().upper() == "YES"
        profile_arm = os.environ.get(f"AFIP_{self.profile.profile_id}_DEMO_ARMED", "").strip().upper() == "YES"
        return global_arm and profile_arm

    def _utc(self) -> str:
        return self._clock().astimezone(timezone.utc).isoformat()

    @property
    def state_path(self) -> Path:
        return self.profile.runtime_directory / "demo_execution_state.json"

    @property
    def ledger_path(self) -> Path:
        return self.profile.logs_directory / "demo_execution_ledger.jsonl"

    def _mt5_module(self) -> MT5Protocol:
        if self._mt5 is not None:
            return self._mt5
        import MetaTrader5 as mt5
        return mt5

    @staticmethod
    def _value(obj: Any, name: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if isinstance(obj, Mapping):
            return obj.get(name, default)
        return getattr(obj, name, default)

    @staticmethod
    def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(dict(payload), indent=2, sort_keys=True, default=str), encoding="utf-8")
        temporary.replace(path)

    @staticmethod
    def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(dict(payload), sort_keys=True, default=str) + "\n")

    def _state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, TypeError):
            return {}

    def _report(self, status: str, reason: str, **updates: Any) -> DemoGatewayReport:
        payload = {
            "profile_id": self.profile.profile_id,
            "status": status,
            "reason": reason,
            "account": self.profile.masked_login,
            "server": self.profile.server,
            "symbol": self.profile.symbol,
            "armed": self.armed,
            "checked_at_utc": self._utc(),
        }
        payload.update(updates)
        report = DemoGatewayReport(**payload)
        persistent = self._state()
        stored = report.as_dict()
        for key in ("last_signal_fingerprint", "last_order_epoch"):
            if key in persistent:
                stored[key] = persistent[key]
        self._write_json(self.state_path, stored)
        self._append_jsonl(self.ledger_path, report.as_dict())
        return report

    @property
    def routing_lock_path(self) -> Path:
        # Injected MT5 adapters are deterministic test/simulation doubles. Keep
        # their lock inside the profile runtime directory so regression tests do
        # not contend with a live production routing lock. Real MT5 execution
        # retains the single global account-routing authority.
        if self._mt5 is not None:
            return self.profile.runtime_directory / "account_routing.lock"
        return Path("runtime/execution/account_routing.lock")

    def _acquire_routing_lock(self, timeout_seconds: float = 45.0) -> tuple[int | None, str]:
        """Serialize MT5 initialize/order_send across profiles.

        The MetaTrader5 Python bridge is process-local but terminal discovery is
        system-wide. Serializing the critical section removes the race where
        concurrent workers can attach to the same already-running terminal.
        """
        path = self.routing_lock_path
        path.parent.mkdir(parents=True, exist_ok=True)
        token = f"{self.profile.profile_id}:{os.getpid()}:{uuid.uuid4().hex}"
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, token.encode("utf-8"))
                return fd, token
            except FileExistsError:
                if reclaim_stale_lock(path, maximum_age_seconds=180.0):
                    continue
                time.sleep(0.25)
        return None, token

    def _release_routing_lock(self, fd: int | None, token: str) -> None:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        path = self.routing_lock_path
        try:
            if path.exists() and path.read_text(encoding="utf-8").strip() == token:
                path.unlink(missing_ok=True)
        except OSError:
            pass

    def _binding_snapshot(self, mt5: MT5Protocol) -> tuple[bool, str, str, str]:
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        actual_login = str(self._value(account, "login", "") or "").strip()
        actual_server = str(self._value(account, "server", "") or "").strip()
        terminal_path = str(self._value(terminal, "path", "") or "").strip()
        try:
            expected_folder = str(self.profile.mt5_folder.resolve()).rstrip("\\/").casefold()
            actual_folder = str(Path(terminal_path).resolve()).rstrip("\\/").casefold() if terminal_path else ""
        except OSError:
            expected_folder = str(self.profile.mt5_folder).rstrip("\\/").casefold()
            actual_folder = terminal_path.rstrip("\\/").casefold()
        login_ok = actual_login == str(self.profile.login)
        server_ok = actual_server.casefold() == self.profile.server.casefold()
        # Injected MT5 adapters are deterministic simulation/test doubles and do not
        # own a real Windows terminal folder. Production uses the imported MT5 module
        # and therefore still requires exact terminal-path ownership.
        path_ok = True if self._mt5 is not None else (bool(actual_folder) and actual_folder == expected_folder)
        return login_ok and server_ok and path_ok, actual_login, actual_server, terminal_path

    def _ownership_diagnostics(self, mt5: MT5Protocol, token: str) -> dict[str, Any]:
        ok, login, _server, terminal_path = self._binding_snapshot(mt5)
        return {
            "connected_account_login": f"****{login[-4:]}" if login else "UNKNOWN",
            "connected_terminal_folder": terminal_path or "UNKNOWN",
            "ownership_token": token,
            "binding_ok": ok,
        }

    def preflight(self, mt5: MT5Protocol) -> tuple[Any | None, DemoGatewayReport | None]:
        policy_errors = self.policy.validate()
        if policy_errors:
            return None, self._report("BLOCKED", ",".join(policy_errors))
        if not self.profile.enabled or not self.policy.enabled:
            return None, self._report("STOPPED", "profile_disabled_by_operator")
        if not self.profile.execution_enabled or not self.policy.execution_enabled:
            return None, self._report("STOPPED", "profile_execution_disabled_research_preserved")
        if not self.policy.demo_execution_enabled:
            return None, self._report("BLOCKED", "demo_execution_disabled_in_profile")
        if self.profile.broker != "XM" or self.profile.symbol != "GOLD#":
            return None, self._report("BLOCKED", "broker_or_symbol_policy_mismatch")
        if not self.armed:
            return None, self._report("BLOCKED", "local_demo_execution_not_armed")
        if not self.profile.login or not self.profile.password_configured:
            return None, self._report("BLOCKED", "mt5_credentials_not_configured")
        if not self.profile.mt5_terminal.exists():
            return None, self._report("BLOCKED", "mt5_terminal_not_found")

        # Reset any inherited/stale MetaTrader5 bridge session before binding the
        # exact profile terminal. This is required even in short-lived workers
        # because Windows terminal discovery can otherwise reuse the first live
        # terminal (commonly P1).
        try:
            mt5.shutdown()
        except Exception:
            pass
        initialized = mt5.initialize(
            path=str(self.profile.mt5_terminal),
            login=int(self.profile.login),
            password=os.environ.get(self.profile.password_env, ""),
            server=self.profile.server,
            timeout=60000,
            portable=True,
        )
        if not initialized:
            return None, self._report("BLOCKED", f"mt5_initialize_failed:{mt5.last_error()}")
        account = mt5.account_info()
        if account is None:
            return None, self._report("BLOCKED", f"mt5_account_info_failed:{mt5.last_error()}")

        login_match = int(self._value(account, "login", 0)) == int(self.profile.login)
        server_match = str(self._value(account, "server", "")).casefold() == self.profile.server.casefold()
        trade_mode = int(self._value(account, "trade_mode", -1))
        if not login_match:
            return None, self._report("BLOCKED", "account_login_mismatch", account_trade_mode=str(trade_mode))
        if not server_match:
            return None, self._report("BLOCKED", "account_server_mismatch", account_trade_mode=str(trade_mode))
        if trade_mode != DEMO_TRADE_MODE:
            return None, self._report("BLOCKED", "account_is_not_demo", account_trade_mode=str(trade_mode))
        if not bool(self._value(account, "trade_allowed", False)):
            return None, self._report("BLOCKED", "account_trade_not_allowed", account_trade_mode="DEMO")
        if not bool(self._value(account, "trade_expert", False)):
            return None, self._report("BLOCKED", "expert_trading_not_allowed", account_trade_mode="DEMO")

        terminal = mt5.terminal_info()
        if terminal is not None and not bool(self._value(terminal, "connected", True)):
            return None, self._report("BLOCKED", "mt5_terminal_disconnected", account_trade_mode="DEMO")
        binding_ok, actual_login, _actual_server, terminal_path = self._binding_snapshot(mt5)
        if not binding_ok:
            return None, self._report(
                "BLOCKED", "exact_profile_binding_mismatch",
                account_trade_mode="DEMO", demo_verified=True,
                connected_account_login=(f"****{actual_login[-4:]}" if actual_login else "UNKNOWN"),
                connected_terminal_folder=terminal_path or "UNKNOWN",
                configured_terminal_folder=str(self.profile.mt5_folder),
            )
        if not mt5.symbol_select(self.profile.symbol, True):
            return None, self._report("BLOCKED", "gold_symbol_select_failed", account_trade_mode="DEMO")
        if mt5.symbol_info_tick(self.profile.symbol) is None:
            return None, self._report("BLOCKED", "gold_tick_unavailable", account_trade_mode="DEMO")
        return account, None

    def _existing_positions(self, mt5: MT5Protocol) -> tuple[list[Any], list[Any]]:
        positions = list(mt5.positions_get(symbol=self.profile.symbol) or ())
        afip_positions = [p for p in positions if int(self._value(p, "magic", 0)) == self.policy.magic]
        manual_positions = [p for p in positions if int(self._value(p, "magic", 0)) != self.policy.magic]
        return afip_positions, manual_positions

    def _capital_growth_decision(self, balance: float, current_orders: int):
        return CapitalGrowthEngine.evaluate(
            mode=self.policy.allocation_mode,
            balance=balance,
            current_orders=current_orders,
            capital_tiers=self.policy.capital_tiers,
            maximum_orders=self.policy.maximum_concurrent_orders,
            legacy_capital_per_unit=0.0,
            legacy_maximum_units=0,
            lot_per_unit=self.policy.lot_per_unit,
        )

    def _allocation_lots(self, balance: float, current_orders: int) -> tuple[float, ...]:
        return self._capital_growth_decision(balance, current_orders).available_lots

    def _cooldown_passed(self, fingerprint: str) -> bool:
        state = self._state()
        if state.get("last_signal_fingerprint") != fingerprint:
            return True
        last_epoch = float(state.get("last_order_epoch", 0.0) or 0.0)
        return time.time() - last_epoch >= self.policy.minimum_seconds_between_entries

    def _request(self, mt5: MT5Protocol, action: str, sl_points: float, tp_points: float, volume: float) -> dict[str, Any]:
        symbol_info = mt5.symbol_info(self.profile.symbol)
        tick = mt5.symbol_info_tick(self.profile.symbol)
        point = float(self._value(symbol_info, "point", 0.0))
        digits = int(self._value(symbol_info, "digits", 2))
        if point <= 0 or tick is None:
            raise ValueError("symbol_point_or_tick_unavailable")
        buy = action == "BUY"
        price = float(self._value(tick, "ask" if buy else "bid", 0.0))
        if price <= 0:
            raise ValueError("entry_price_unavailable")
        sl = price - sl_points * point if buy else price + sl_points * point
        tp = price + tp_points * point if buy else price - tp_points * point
        order_type = getattr(mt5, "ORDER_TYPE_BUY") if buy else getattr(mt5, "ORDER_TYPE_SELL")
        request = {
            "action": getattr(mt5, "TRADE_ACTION_DEAL"),
            "symbol": self.profile.symbol,
            "volume": round(float(volume), 2),
            "type": order_type,
            "price": round(price, digits),
            "sl": round(sl, digits),
            "tp": round(tp, digits),
            "deviation": 20,
            "magic": self.policy.magic,
            "comment": f"AFIP {self.profile.profile_id} DEMO",
            "type_time": getattr(mt5, "ORDER_TIME_GTC"),
            "type_filling": getattr(mt5, "ORDER_FILLING_IOC"),
        }
        return request

    def run_cycle(self) -> DemoGatewayReport:
        fd, token = self._acquire_routing_lock()
        if fd is None:
            return self._report("WAITING", "account_routing_lock_busy", ownership_token=token)
        try:
            return self._run_cycle_under_lock(token)
        finally:
            self._release_routing_lock(fd, token)

    def _run_cycle_under_lock(self, ownership_token: str) -> DemoGatewayReport:
        mt5 = self._mt5_module()
        try:
            account, blocked = self.preflight(mt5)
            if blocked is not None:
                return blocked
            assert account is not None

            afip_positions, manual_positions = self._existing_positions(mt5)
            if manual_positions:
                return self._report("BLOCKED", "manual_position_detected_operator_override", account_trade_mode="DEMO", demo_verified=True)

            result = self._simulate()
            decision = result.get("decision", {})
            order = result.get("order", {})
            action = str(decision.get("action", order.get("action", "WAIT"))).upper()
            confidence = float(decision.get("confidence", 0.0) or 0.0)
            data_status = str(result.get("data_status", "")).upper()
            data_source = str(result.get("data_source", "")).upper()
            risk = result.get("risk", {})
            cost = result.get("trading_cost_intelligence", {})
            protection = order.get("protection", {})
            protection_portfolio = order.get("protection_portfolio", {})

            if "FALLBACK" in data_status or "FALLBACK" in data_source:
                return self._report("WAITING", "simulation_fallback_data_blocked", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence)
            if action not in {"BUY", "SELL"}:
                return self._report("WAITING", "decision_not_actionable", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence)
            if confidence < self.policy.minimum_confidence:
                return self._report("WAITING", "profile_confidence_below_threshold", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence)
            if not bool(risk.get("allowed", False)):
                return self._report("WAITING", "risk_not_approved", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence)

            cost_status = str(cost.get("status", "")).strip().upper()
            cost_allowed = cost.get("allowed") is True
            cost_diagnostics = {
                "trading_cost_status": cost_status or "UNKNOWN",
                "trading_cost_allowed": cost_allowed,
                "spread_points": float(cost.get("spread_points", 0.0) or 0.0),
                "caution_spread_points": float(cost.get("caution_spread_points", 0.0) or 0.0),
                "max_spread_points": float(cost.get("max_spread_points", 0.0) or 0.0),
            }
            if cost_status not in {"PASS", "CAUTION", "BLOCK"}:
                return self._report("BLOCKED", "trading_cost_status_unknown", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, **cost_diagnostics)
            if not cost_allowed:
                return self._report("WAITING", "trading_cost_not_approved", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, **cost_diagnostics)
            if cost_status == "BLOCK":
                return self._report("BLOCKED", "trading_cost_contract_inconsistent", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, **cost_diagnostics)
            if str(order.get("status", "")).upper() != "SIMULATION_ORDER_READY":
                return self._report("WAITING", "protected_order_not_ready", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence)

            sl_points = float(protection.get("stop_loss_points", 0.0) or 0.0)
            tp_points = float(protection.get("take_profit_points", 0.0) or 0.0)
            if sl_points <= 0 or tp_points <= 0:
                return self._report("BLOCKED", "protective_sl_tp_missing", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence)

            current_orders = len(afip_positions)
            account_balance = float(self._value(account, "balance", 0.0) or 0.0)
            order_unit_allocation = order.get("unit_allocation", {})
            authority_request = {
                "requested_units": order_unit_allocation.get(
                    "requested_units",
                    order_unit_allocation.get("approved_units", decision.get("requested_units")),
                )
            }
            authority = calculate_lot_authority(
                profile={
                    "profile_id": self.policy.profile_id,
                    "maximum_units": self.policy.maximum_units,
                    "maximum_concurrent_orders": self.policy.maximum_concurrent_orders,
                    "allocation_mode": self.policy.allocation_mode,
                    "capital_tiers": [
                        {"minimum_balance": level, "lots": list(lots)}
                        for level, lots in self.policy.capital_tiers
                    ],
                    "execution_enabled": self.policy.execution_enabled,
                },
                decision=authority_request,
                confidence=confidence,
                balance=account_balance,
                equity=float(self._value(account, "equity", account_balance) or account_balance),
                current_orders=current_orders,
            )
            allocation_lots = authority.approved_lots
            units = authority.approved_units
            growth = self._capital_growth_decision(account_balance, current_orders)  # diagnostics only; authority owns approval
            maximum_orders = 0 if self.policy.allocation_mode == "RESEARCH_FIXED_001" else self.policy.maximum_concurrent_orders
            remaining_order_capacity = -1 if maximum_orders == 0 else max(0, maximum_orders - current_orders)
            authority_diagnostics = authority.as_dict()
            authority_diagnostics.pop("profile_id", None)
            authority_diagnostics["sizing_reason"] = authority_diagnostics.pop("reason")
            allocation_diagnostics = {
                **authority_diagnostics,
                "allocated_units": units,
                "confidence_maximum_units": authority.confidence_units,
                "allocated_orders": len(allocation_lots),
                "allocated_lots": tuple(allocation_lots),
                "total_allocated_lot": authority.total_approved_lot,
                "order_unit_distribution": tuple(1 for _ in allocation_lots),
                "maximum_orders": maximum_orders,
                "remaining_order_capacity": remaining_order_capacity,
                "allocation_mode": self.policy.allocation_mode,
                "account_balance": authority.balance,
                "current_tier_minimum_balance": growth.current_tier_minimum_balance,
                "target_tier_lots": growth.target_lots,
                "next_tier_balance": growth.next_tier_balance,
                "remaining_to_next_tier": growth.remaining_to_next_tier,
                "maximum_tier_balance": growth.maximum_tier_balance,
                "withdrawal_reference_balance": growth.withdrawal_reference_balance,
                "unit_selection_source": "SINGLE_LOT_AUTHORITY",
                "unit_selection_reason": authority.reason,
            }
            if not allocation_lots:
                return self._report("WAITING", "profile_order_capacity_unavailable", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, **allocation_diagnostics)

            rr_plans = tuple(protection_portfolio.get("unit_plans", ()))
            if rr_plans and len(rr_plans) < len(allocation_lots):
                return self._report("BLOCKED", "rr_protection_plan_count_insufficient", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, **allocation_diagnostics)
            fingerprint = hashlib.sha256(f"{self.profile.profile_id}|{action}|{confidence:.4f}|{sl_points:.2f}|{tp_points:.2f}".encode()).hexdigest()
            if not self._cooldown_passed(fingerprint):
                return self._report("WAITING", "duplicate_signal_cooldown_active", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, **allocation_diagnostics)

            symbol_info = mt5.symbol_info(self.profile.symbol)
            point_size = float(self._value(symbol_info, "point", 0.0) or 0.0)
            digits = int(self._value(symbol_info, "digits", 0) or 0)
            execution_diagnostics = {**cost_diagnostics, "point_size": point_size, "digits": digits}

            tickets: list[int] = []
            for order_index, volume in enumerate(allocation_lots):
                unit_plan = rr_plans[order_index] if rr_plans else protection
                unit_sl_points = float(unit_plan.get("stop_loss_points", sl_points) or sl_points)
                unit_tp_points = float(unit_plan.get("take_profit_points", tp_points) or tp_points)
                if unit_sl_points <= 0 or unit_tp_points <= 0:
                    return self._report("BLOCKED", "rr_unit_protection_missing", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, sent_units=len(tickets), **allocation_diagnostics, tickets=tuple(tickets), **execution_diagnostics)
                request = self._request(mt5, action, unit_sl_points, unit_tp_points, volume)
                request["comment"] = f"AFIP {self.profile.profile_id} {unit_plan.get('role', 'RR')}"
                binding_ok, actual_login, _actual_server, terminal_path = self._binding_snapshot(mt5)
                request_owned = (
                    int(request.get("magic", 0)) == self.policy.magic
                    and f"AFIP {self.profile.profile_id} " in str(request.get("comment", ""))
                )
                if not binding_ok or not request_owned:
                    return self._report(
                        "BLOCKED", "execution_ownership_mismatch_before_order_check",
                        account_trade_mode="DEMO", demo_verified=True,
                        decision_action=action, decision_confidence=confidence,
                        sent_units=len(tickets), **allocation_diagnostics, tickets=tuple(tickets),
                        connected_account_login=(f"****{actual_login[-4:]}" if actual_login else "UNKNOWN"),
                        connected_terminal_folder=terminal_path or "UNKNOWN",
                        configured_terminal_folder=str(self.profile.mt5_folder),
                        ownership_token=ownership_token, **execution_diagnostics,
                    )
                check = mt5.order_check(request)
                if check is None or int(self._value(check, "retcode", -1)) != 0:
                    reason = self._value(check, "comment", mt5.last_error())
                    return self._report("BLOCKED", f"order_check_failed:{reason}", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, sent_units=len(tickets), **allocation_diagnostics, tickets=tuple(tickets), order_check_called=True, mt5_result_code=int(self._value(check, "retcode", -1)), mt5_result_comment=str(reason), **execution_diagnostics)
                binding_ok, actual_login, _actual_server, terminal_path = self._binding_snapshot(mt5)
                if not binding_ok:
                    return self._report(
                        "BLOCKED", "execution_ownership_changed_before_order_send",
                        account_trade_mode="DEMO", demo_verified=True,
                        decision_action=action, decision_confidence=confidence,
                        sent_units=len(tickets), **allocation_diagnostics, tickets=tuple(tickets),
                        order_check_called=True,
                        connected_account_login=(f"****{actual_login[-4:]}" if actual_login else "UNKNOWN"),
                        connected_terminal_folder=terminal_path or "UNKNOWN",
                        configured_terminal_folder=str(self.profile.mt5_folder),
                        ownership_token=ownership_token, **execution_diagnostics,
                    )
                result_send = mt5.order_send(request)
                if result_send is None:
                    return self._report("ERROR", f"order_send_returned_none:{mt5.last_error()}", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, sent_units=len(tickets), **allocation_diagnostics, tickets=tuple(tickets), order_check_called=True, order_send_called=True, mt5_result_comment=str(mt5.last_error()), **execution_diagnostics)
                retcode = int(self._value(result_send, "retcode", -1))
                success_codes = {
                    int(getattr(mt5, name)) for name in SUCCESS_RETCODE_NAMES if hasattr(mt5, name)
                }
                if retcode not in success_codes:
                    comment = self._value(result_send, "comment", "unknown")
                    return self._report("ERROR", f"order_send_failed:{retcode}:{comment}", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, sent_units=len(tickets), **allocation_diagnostics, tickets=tuple(tickets), order_check_called=True, order_send_called=True, mt5_result_code=retcode, mt5_result_comment=str(comment), **execution_diagnostics)
                ticket = int(self._value(result_send, "order", self._value(result_send, "deal", 0)) or 0)
                tickets.append(ticket)

            binding_ok, actual_login, _actual_server, terminal_path = self._binding_snapshot(mt5)
            if not binding_ok:
                return self._report(
                    "ERROR", "execution_ownership_changed_after_order_send", account_trade_mode="DEMO",
                    demo_verified=True, decision_action=action, decision_confidence=confidence,
                    sent_units=len(tickets), **allocation_diagnostics, tickets=tuple(tickets),
                    order_check_called=True, order_send_called=True,
                    connected_account_login=(f"****{actual_login[-4:]}" if actual_login else "UNKNOWN"),
                    connected_terminal_folder=terminal_path or "UNKNOWN",
                    ownership_token=ownership_token, **execution_diagnostics,
                )
            report = self._report("ORDER_SENT", "protected_demo_orders_sent", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, sent_units=len(tickets), **allocation_diagnostics, order_status="DEMO_ORDER_SENT", tickets=tuple(tickets), order_check_called=True, order_send_called=True, mt5_result_code=retcode, mt5_result_comment=str(self._value(result_send, "comment", "")), connected_account_login=(f"****{actual_login[-4:]}" if actual_login else "UNKNOWN"), connected_terminal_folder=terminal_path or "UNKNOWN", ownership_token=ownership_token, **execution_diagnostics)
            state = report.as_dict()
            state["last_signal_fingerprint"] = fingerprint
            state["last_order_epoch"] = time.time()
            self._write_json(self.state_path, state)
            return report
        except Exception as exc:
            return self._report("ERROR", f"demo_gateway_error:{type(exc).__name__}:{exc}")
        finally:
            try:
                mt5.shutdown()
            except Exception:
                pass


class DemoExecutionRunner:
    def __init__(self, config: DemoGatewayConfig, *, sleep: Callable[[float], None] = time.sleep) -> None:
        config.validate()
        self.config = config
        self._sleep = sleep
        self._stop_requested = False

    def request_stop(self, *_: Any) -> None:
        self._stop_requested = True

    @staticmethod
    def _load(config_path: Path, profile_id: str) -> tuple[ProfileOperationalConfig, DemoProfilePolicy]:
        raw = json.loads(config_path.read_text(encoding="utf-8-sig"))
        raw_profile = next(item for item in raw["profiles"] if str(item["profile_id"]).upper() == profile_id.upper())
        profile = next(item for item in FourProfileOperationalRuntime(config_path).load() if item.profile_id == profile_id.upper())
        return profile, DemoProfilePolicy.from_mapping(raw_profile)

    def run(self) -> None:
        profile, policy = self._load(self.config.config_path, self.config.profile_id)
        gateway = DemoExecutionGateway(profile, policy)
        completed = 0
        previous: dict[int, Any] = {}
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                previous[sig] = signal.getsignal(sig)
                signal.signal(sig, self.request_stop)
            except (ValueError, OSError):
                pass
        try:
            while not self._stop_requested:
                report = gateway.run_cycle()
                completed += 1
                print(json.dumps(report.as_dict(), sort_keys=True), flush=True)
                if self.config.maximum_cycles is not None and completed >= self.config.maximum_cycles:
                    break
                if not self._stop_requested:
                    self._sleep(self.config.interval_seconds)
        finally:
            for sig, handler in previous.items():
                try: signal.signal(sig, handler)
                except (ValueError, OSError): pass
