"""Isolated MT5 terminal health checks for AFIP four-profile operations.

This module only verifies terminal connectivity and market data availability.
It never enables live execution and never sends an order.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Callable, Protocol

from .runtime import LOCKED_EXECUTION, NO_ORDER_SENT, FourProfileOperationalRuntime, ProfileOperationalConfig


class MT5Adapter(Protocol):
    def initialize(self, **kwargs: Any) -> bool: ...
    def shutdown(self) -> None: ...
    def account_info(self) -> Any: ...
    def terminal_info(self) -> Any: ...
    def symbol_select(self, symbol: str, enable: bool) -> bool: ...
    def symbol_info_tick(self, symbol: str) -> Any: ...
    def last_error(self) -> Any: ...


@dataclass(frozen=True)
class MT5ProfileHealth:
    profile_id: str
    enabled: bool
    connection_status: str
    terminal_exists: bool
    initialized: bool
    authenticated: bool
    account_match: bool
    server_match: bool
    symbol_available: bool
    tick_available: bool
    latency_ms: float | None
    reconnect_attempts: int
    account: str
    server: str
    terminal_path: str
    reason: str
    checked_at_utc: str
    execution: str = LOCKED_EXECUTION
    order_status: str = NO_ORDER_SENT
    direct_execution: bool = False
    live_execution: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MT5MultiTerminalConnectionManager:
    def __init__(
        self,
        config_path: str | Path = "config/four_profile_demo.json",
        adapter_factory: Callable[[], MT5Adapter] | None = None,
    ) -> None:
        self.operations = FourProfileOperationalRuntime(config_path)
        self.adapter_factory = adapter_factory or self._default_adapter_factory

    @staticmethod
    def _default_adapter_factory() -> MT5Adapter:
        import MetaTrader5 as mt5
        return mt5

    @staticmethod
    def _value(obj: Any, name: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    @staticmethod
    def _masked(value: str) -> str:
        return "NOT_CONFIGURED" if not value else f"****{value[-4:]}"

    def _write_health(self, profile: ProfileOperationalConfig, health: MT5ProfileHealth) -> None:
        profile.runtime_directory.mkdir(parents=True, exist_ok=True)
        (profile.runtime_directory / "mt5_health.json").write_text(
            json.dumps(health.as_dict(), indent=2), encoding="utf-8"
        )

    def check_profile(self, profile: ProfileOperationalConfig, reconnect_attempts: int = 1) -> MT5ProfileHealth:
        checked_at = datetime.now(timezone.utc).isoformat()
        if not profile.enabled:
            health = MT5ProfileHealth(
                profile.profile_id, False, "STOPPED", profile.mt5_terminal.exists(), False, False,
                False, False, False, False, None, 0, profile.masked_login, profile.server,
                str(profile.mt5_terminal), "Profile disabled by operator", checked_at,
            )
            self._write_health(profile, health)
            return health
        if not profile.mt5_terminal.exists():
            health = MT5ProfileHealth(
                profile.profile_id, True, "BLOCKED", False, False, False, False, False, False,
                False, None, 0, profile.masked_login, profile.server, str(profile.mt5_terminal),
                "MT5 terminal64.exe not found", checked_at,
            )
            self._write_health(profile, health)
            return health
        if not profile.login or not profile.password_configured:
            health = MT5ProfileHealth(
                profile.profile_id, True, "BLOCKED", True, False, False, False, False, False,
                False, None, 0, profile.masked_login, profile.server, str(profile.mt5_terminal),
                "MT5 credentials are not configured in environment variables", checked_at,
            )
            self._write_health(profile, health)
            return health

        initialized = False
        adapter: MT5Adapter | None = None
        attempts_used = 0
        started = time.perf_counter()
        last_error: Any = None
        try:
            adapter = self.adapter_factory()
            for attempt in range(max(1, reconnect_attempts + 1)):
                attempts_used = attempt
                initialized = bool(adapter.initialize(
                    path=str(profile.mt5_terminal),
                    login=int(profile.login),
                    password=__import__("os").environ.get(profile.password_env, ""),
                    server=profile.server,
                    portable=True,
                ))
                if initialized:
                    break
                last_error = adapter.last_error()
                try:
                    adapter.shutdown()
                except Exception:
                    pass
                if attempt < reconnect_attempts:
                    time.sleep(0.15)
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            if not initialized:
                reason = f"MT5 initialize failed: {last_error}"
                health = MT5ProfileHealth(
                    profile.profile_id, True, "DISCONNECTED", True, False, False, False, False,
                    False, False, latency_ms, attempts_used, profile.masked_login, profile.server,
                    str(profile.mt5_terminal), reason, checked_at,
                )
                self._write_health(profile, health)
                return health

            account_info = adapter.account_info()
            terminal_info = adapter.terminal_info()
            actual_login = str(self._value(account_info, "login", ""))
            actual_server = str(self._value(account_info, "server", ""))
            authenticated = account_info is not None
            account_match = authenticated and actual_login == profile.login
            server_match = authenticated and actual_server.casefold() == profile.server.casefold()
            symbol_available = bool(adapter.symbol_select(profile.symbol, True))
            tick_available = adapter.symbol_info_tick(profile.symbol) is not None if symbol_available else False
            connected = bool(self._value(terminal_info, "connected", initialized))
            ok = all((authenticated, account_match, server_match, symbol_available, tick_available, connected))
            reason_parts: list[str] = []
            if not authenticated: reason_parts.append("account information unavailable")
            if authenticated and not account_match: reason_parts.append("account does not match profile")
            if authenticated and not server_match: reason_parts.append("server does not match profile")
            if not connected: reason_parts.append("terminal disconnected")
            if not symbol_available: reason_parts.append("GOLD# unavailable in Market Watch")
            elif not tick_available: reason_parts.append("GOLD# tick unavailable")
            health = MT5ProfileHealth(
                profile.profile_id, True, "CONNECTED" if ok else "DEGRADED", True, True,
                authenticated, account_match, server_match, symbol_available, tick_available,
                latency_ms, attempts_used, self._masked(actual_login or profile.login),
                actual_server or profile.server, str(profile.mt5_terminal),
                "MT5 terminal connected and GOLD# data ready" if ok else "; ".join(reason_parts),
                checked_at,
            )
            self._write_health(profile, health)
            return health
        except Exception as exc:
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            health = MT5ProfileHealth(
                profile.profile_id, True, "ERROR", True, initialized, False, False, False, False,
                False, latency_ms, attempts_used, profile.masked_login, profile.server,
                str(profile.mt5_terminal), f"MT5 health check error: {type(exc).__name__}: {exc}", checked_at,
            )
            self._write_health(profile, health)
            return health
        finally:
            if adapter is not None:
                try:
                    adapter.shutdown()
                except Exception:
                    pass

    def check(self, selected: list[str] | None = None, reconnect_attempts: int = 1) -> dict[str, Any]:
        profiles = self.operations.load()
        errors = self.operations.validate(profiles)
        selected_ids = {value.upper() for value in selected} if selected else None
        results = []
        for profile in profiles:
            if selected_ids is not None and profile.profile_id not in selected_ids:
                continue
            results.append(self.check_profile(profile, reconnect_attempts).as_dict())
        connected = sum(1 for item in results if item["connection_status"] == "CONNECTED")
        return {
            "status": "READY" if not errors else "BLOCKED",
            "connected_profiles": connected,
            "checked_profiles": len(results),
            "profiles": results,
            "validation_errors": list(errors),
            "execution": LOCKED_EXECUTION,
            "order_status": NO_ORDER_SENT,
            "direct_execution": False,
            "live_execution": False,
        }
