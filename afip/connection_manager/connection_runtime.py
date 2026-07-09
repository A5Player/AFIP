"""Connection Manager runtime for dashboard status."""

from __future__ import annotations

from typing import Any, Mapping

from .connection_report import ConnectionManagerReport

_SAFE_EXECUTION_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "DEMO", "DEMO_TRADING", "LOCKED_SIMULATION_ONLY"}


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class ConnectionManagerRuntime:
    """Evaluate Internet, MT5, broker, and system runtime readiness."""

    def evaluate_one(self, record: Mapping[str, Any]) -> ConnectionManagerReport:
        execution_mode = str(record.get("execution_mode", "LOCKED_SIMULATION_ONLY")).strip().upper()
        internet_status = str(record.get("internet_status", "CONNECTED")).strip().upper() or "UNKNOWN"
        mt5_status = str(record.get("mt5_status", "CONNECTED")).strip().upper() or "UNKNOWN"
        broker_status = str(record.get("broker_status", "XM_READY")).strip().upper() or "UNKNOWN"
        market_status = str(record.get("market_status", "OPEN")).strip().upper() or "UNKNOWN"
        trading_session = str(record.get("trading_session", "LONDON_NEW_YORK_OVERLAP")).strip().upper() or "UNKNOWN"
        disconnect_count = max(0, _int(record.get("internet_disconnect_count", 0), 0))
        disconnect_duration = max(0, _int(record.get("internet_disconnect_duration_seconds", 0), 0))
        reconnect_count = max(0, _int(record.get("reconnect_count", 0), 0))
        cpu = max(0.0, _float(record.get("cpu_percent", 0.0), 0.0))
        ram = max(0.0, _float(record.get("ram_percent", 0.0), 0.0))
        disk = max(0.0, _float(record.get("disk_percent", 0.0), 0.0))
        runtime_seconds = max(0, _int(record.get("runtime_seconds", 0), 0))
        profile_name = str(record.get("profile_name", record.get("profile", "Conservative"))).strip() or "Conservative"

        reason = "connection_manager_ready"
        gate = "CONNECTION_MANAGER_READY"
        status = "READY"
        waiting_reason = "-"
        if execution_mode not in _SAFE_EXECUTION_MODES:
            status, reason, gate, waiting_reason = "BLOCKED", "live_execution_not_allowed_for_connection_manager", "BLOCKED", "safe_execution_mode_required"
        elif internet_status != "CONNECTED":
            status, reason, gate, waiting_reason = "WAITING", "internet_connection_wait", "WAITING", "internet_disconnected"
        elif mt5_status != "CONNECTED":
            status, reason, gate, waiting_reason = "WAITING", "mt5_connection_wait", "WAITING", "mt5_not_connected"
        elif broker_status not in {"XM_READY", "CONNECTED", "READY"}:
            status, reason, gate, waiting_reason = "WAITING", "broker_connection_wait", "WAITING", "broker_not_ready"
        elif market_status == "CLOSED":
            status, reason, gate, waiting_reason = "WAITING", "market_closed_wait", "WAITING", "market_closed"
        elif max(cpu, ram, disk) >= 95:
            status, reason, gate, waiting_reason = "REVIEW", "system_resource_review", "REVIEW", "system_resource_near_limit"

        return ConnectionManagerReport(
            status=status,
            reason=reason,
            connection_gate=gate,
            internet_status=internet_status,
            internet_disconnect_count=disconnect_count,
            internet_disconnect_duration_seconds=disconnect_duration,
            reconnect_count=reconnect_count,
            mt5_status=mt5_status,
            broker_status=broker_status,
            market_status=market_status,
            trading_session=trading_session,
            profile_name=profile_name,
            cpu_percent=cpu,
            ram_percent=ram,
            disk_percent=disk,
            runtime_seconds=runtime_seconds,
            waiting_reason=waiting_reason,
        )

    def explain_one(self, record: Mapping[str, Any]) -> ConnectionManagerReport:
        return self.evaluate_one(record)
