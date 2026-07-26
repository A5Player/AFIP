"""Isolated MT5 terminal health checks for AFIP four-profile operations.

This module only verifies terminal connectivity and market data availability.
It never enables live execution and never sends an order.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import os
import subprocess
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
    currency: str = "DATA_UNAVAILABLE"
    balance: float | None = None
    equity: float | None = None
    margin: float | None = None
    free_margin: float | None = None
    floating_profit: float | None = None
    # Backward-compatible schema aliases retained for existing consumers.
    margin_free: float | None = None
    profit: float | None = None
    trade_allowed: bool | None = None
    positions_total: int | None = None
    orders_total: int | None = None
    bid: float | None = None
    ask: float | None = None
    spread_points: float | None = None
    digits: int | None = None
    point_size: float | None = None
    monitoring_mode: str = "ACTIVE"
    process_alive: bool | None = None
    evidence_kind: str = "LIVE"
    snapshot_checked_at_utc: str | None = None
    snapshot_age_seconds: int | None = None

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


    @staticmethod
    def _normal_path(value: str | Path) -> str:
        text = os.path.abspath(os.path.expandvars(str(value))).replace("/", "\\")
        return os.path.normcase(text.rstrip("\\"))

    @classmethod
    def _running_terminal_paths(cls) -> set[str]:
        """Return terminal64.exe paths without starting or attaching to MT5."""
        paths: set[str] = set()
        try:
            import psutil  # type: ignore
            for proc in psutil.process_iter(["name", "exe"]):
                try:
                    if str(proc.info.get("name") or "").lower() != "terminal64.exe":
                        continue
                    exe = proc.info.get("exe")
                    if exe:
                        paths.add(cls._normal_path(exe))
                except Exception:
                    continue
        except Exception:
            pass
        if paths or os.name != "nt":
            return paths
        # psutil is optional. PowerShell/CIM is available on supported Windows hosts.
        command = [
            "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
            "$ErrorActionPreference='SilentlyContinue'; "
            "Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\" | "
            "ForEach-Object { $_.ExecutablePath }",
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
            for line in completed.stdout.splitlines():
                line = line.strip()
                if line:
                    paths.add(cls._normal_path(line))
        except Exception:
            pass
        return paths

    def _terminal_process_alive(self, terminal_path: str | Path) -> bool:
        """Return process truth for one configured terminal without MT5 attachment.

        Kept as a small instance seam for backward-compatible tests and callers;
        the implementation remains the same read-only executable-path authority.
        """
        return self._normal_path(terminal_path) in self._running_terminal_paths()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _write_live_snapshot(self, profile: ProfileOperationalConfig, health: MT5ProfileHealth) -> None:
        profile.runtime_directory.mkdir(parents=True, exist_ok=True)
        (profile.runtime_directory / "mt5_live_snapshot.json").write_text(
            json.dumps(health.as_dict(), indent=2), encoding="utf-8"
        )

    def check_profile_passive(
        self, profile: ProfileOperationalConfig, running_paths: set[str] | None = None
    ) -> MT5ProfileHealth:
        """Observe the configured terminal process. Never call MT5.initialize()."""
        checked = datetime.now(timezone.utc)
        checked_at = checked.isoformat()
        exists = profile.mt5_terminal.exists()
        if running_paths is None:
            alive = exists and self._terminal_process_alive(profile.mt5_terminal)
        else:
            # Preserve a caller-supplied process snapshot while retaining the
            # per-terminal compatibility seam used by focused passive tests.
            alive = exists and self._normal_path(profile.mt5_terminal) in running_paths
            if not alive and running_paths == set():
                alive = exists and self._terminal_process_alive(profile.mt5_terminal)
        snapshot_path = profile.runtime_directory / "mt5_live_snapshot.json"
        snapshot = self._read_json(snapshot_path)
        if not snapshot:
            previous = self._read_json(profile.runtime_directory / "mt5_health.json")
            if str(previous.get("monitoring_mode", "ACTIVE")).upper() == "ACTIVE":
                snapshot = previous
        snapshot_time = snapshot.get("snapshot_checked_at_utc") or snapshot.get("checked_at_utc")
        snapshot_age = None
        if snapshot_time:
            try:
                parsed = datetime.fromisoformat(str(snapshot_time).replace("Z", "+00:00"))
                snapshot_age = max(0, int((checked - parsed.astimezone(timezone.utc)).total_seconds()))
            except (TypeError, ValueError):
                snapshot_age = None
        if not profile.enabled:
            status, reason = "STOPPED", "Profile disabled by operator"
        elif not exists:
            status, reason = "BLOCKED", "Configured terminal64.exe not found"
        elif not alive:
            status, reason = "DISCONNECTED", "Configured MT5 process is not running (passive observation)"
        else:
            status, reason = "CONNECTED_PASSIVE", "Configured MT5 process is running; broker session was not mutated"
        use_snapshot = bool(snapshot)
        def snap(name: str, default: Any = None) -> Any:
            return snapshot.get(name, default) if use_snapshot else default
        health = MT5ProfileHealth(
            profile_id=profile.profile_id, enabled=bool(profile.enabled), connection_status=status,
            terminal_exists=exists, initialized=False, authenticated=False, account_match=False,
            server_match=False, symbol_available=False, tick_available=False, latency_ms=None,
            reconnect_attempts=0, account=str(snap("account", profile.masked_login)),
            server=str(snap("server", profile.server)), terminal_path=str(profile.mt5_terminal),
            reason=reason, checked_at_utc=checked_at, currency=str(snap("currency", "DATA_UNAVAILABLE")),
            balance=snap("balance"), equity=snap("equity"), margin=snap("margin"),
            free_margin=snap("free_margin", snap("margin_free")),
            floating_profit=snap("floating_profit", snap("profit")),
            margin_free=snap("margin_free", snap("free_margin")), profit=snap("profit", snap("floating_profit")),
            trade_allowed=snap("trade_allowed") if alive else False,
            positions_total=snap("positions_total", 0), orders_total=snap("orders_total", 0),
            bid=snap("bid"), ask=snap("ask"), spread_points=snap("spread_points"),
            digits=snap("digits"), point_size=snap("point_size"), monitoring_mode="PASSIVE",
            process_alive=alive, evidence_kind="LAST_SNAPSHOT" if use_snapshot else "PROCESS_ONLY",
            snapshot_checked_at_utc=str(snapshot_time) if snapshot_time else None,
            snapshot_age_seconds=snapshot_age,
        )
        self._write_health(profile, health)
        return health

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
            tick = adapter.symbol_info_tick(profile.symbol) if symbol_available else None
            symbol_info = getattr(adapter, "symbol_info", lambda _s: None)(profile.symbol) if symbol_available else None
            positions = getattr(adapter, "positions_get", lambda **_k: ()) (symbol=profile.symbol) or ()
            orders = getattr(adapter, "orders_get", lambda **_k: ()) (symbol=profile.symbol) or ()
            point_size = self._value(symbol_info, "point")
            bid = self._value(tick, "bid")
            ask = self._value(tick, "ask")
            spread_points = None
            try:
                if point_size and bid is not None and ask is not None:
                    spread_points = round((float(ask) - float(bid)) / float(point_size), 2)
            except (TypeError, ValueError, ZeroDivisionError):
                spread_points = None
            health = replace(
                health,
                currency=str(self._value(account_info, "currency", "DATA_UNAVAILABLE")),
                balance=self._value(account_info, "balance"),
                equity=self._value(account_info, "equity"),
                margin=self._value(account_info, "margin"),
                free_margin=self._value(account_info, "margin_free"),
                floating_profit=self._value(account_info, "profit"),
                margin_free=self._value(account_info, "margin_free"),
                profit=self._value(account_info, "profit"),
                trade_allowed=self._value(account_info, "trade_allowed"),
                positions_total=len(positions),
                orders_total=len(orders),
                bid=bid,
                ask=ask,
                spread_points=spread_points,
                digits=self._value(symbol_info, "digits"),
                point_size=point_size, monitoring_mode="ACTIVE", process_alive=True,
                evidence_kind="LIVE", snapshot_checked_at_utc=checked_at, snapshot_age_seconds=0,
            )
            self._write_live_snapshot(profile, health)
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

    def check(self, selected: list[str] | None = None, reconnect_attempts: int = 1, *, active: bool = True) -> dict[str, Any]:
        profiles = self.operations.load()
        errors = self.operations.validate(profiles)
        selected_ids = {value.upper() for value in selected} if selected else None
        results = []
        running_paths = None if active else self._running_terminal_paths()
        for profile in profiles:
            if selected_ids is not None and profile.profile_id not in selected_ids:
                continue
            health = self.check_profile(profile, reconnect_attempts) if active else self.check_profile_passive(profile, running_paths)
            results.append(health.as_dict())
        connected = sum(1 for item in results if item["connection_status"] in {"CONNECTED", "CONNECTED_PASSIVE"})
        return {
            "status": "READY" if not errors else "BLOCKED",
            "connected_profiles": connected,
            "checked_profiles": len(results),
            "profiles": results,
            "monitoring_mode": "ACTIVE" if active else "PASSIVE",
            "validation_errors": list(errors),
            "execution": LOCKED_EXECUTION,
            "order_status": NO_ORDER_SENT,
            "direct_execution": False,
            "live_execution": False,
        }
