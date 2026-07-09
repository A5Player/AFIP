"""Runtime supervisor for deterministic Windows VPS monitoring."""

from __future__ import annotations

from typing import Any, Mapping

from .event_logger import RuntimeEventLogger
from .recovery_engine import RuntimeRecoveryEngine
from .runtime_models import RuntimeServiceReport


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


class RuntimeServiceManager:
    """Compose supervisor, heartbeat, recovery, and event history reports."""

    def evaluate_one(self, record: Mapping[str, Any]) -> RuntimeServiceReport:
        recovery = RuntimeRecoveryEngine().evaluate_one(record)
        heartbeat_age = max(0, _int(record.get("heartbeat_age_seconds", 0), 0))
        runtime_seconds = max(0, _int(record.get("runtime_seconds", 0), 0))
        restart_count = max(0, _int(record.get("restart_count", 0), 0))
        unexpected_exception_count = max(0, _int(record.get("unexpected_exception_count", 0), 0))
        reconnect_count = max(0, _int(record.get("reconnect_count", 0), 0))
        disconnect_count = max(0, _int(record.get("internet_disconnect_count", 0), 0))
        disconnect_duration = max(0, _int(record.get("internet_disconnect_duration_seconds", 0), 0))
        cpu = max(0.0, _float(record.get("cpu_percent", 0.0), 0.0))
        ram = max(0.0, _float(record.get("ram_percent", 0.0), 0.0))
        disk = max(0.0, _float(record.get("disk_percent", 0.0), 0.0))
        internet_status = str(record.get("internet_status", "CONNECTED")).strip().upper() or "UNKNOWN"
        mt5_status = str(record.get("mt5_status", "CONNECTED")).strip().upper() or "UNKNOWN"
        broker_status = str(record.get("broker_status", "XM_READY")).strip().upper() or "UNKNOWN"
        heartbeat_status = "READY" if heartbeat_age <= 90 else "STALE"
        resource_review = max(cpu, ram, disk) >= 95
        supervisor_status = "READY"
        status = "READY"
        reason = "runtime_service_ready"
        gate = "RUNTIME_SERVICE_READY"
        if recovery.status == "BLOCKED":
            status, reason, gate, supervisor_status = "BLOCKED", recovery.reason, "BLOCKED", "BLOCKED"
        elif recovery.status == "RECOVERING":
            status, reason, gate, supervisor_status = "RECOVERING", recovery.reason, "RECOVERING", "PAUSED"
        elif heartbeat_status == "STALE":
            status, reason, gate, supervisor_status = "REVIEW", "runtime_heartbeat_stale", "REVIEW", "REVIEW"
        elif unexpected_exception_count > 0 or restart_count > 0 or resource_review:
            status, reason, gate, supervisor_status = "REVIEW", "runtime_watchdog_review", "REVIEW", "REVIEW"
        event_history = RuntimeEventLogger().build(record.get("event_history"))
        sections = ("runtime", "internet", "mt5", "broker", "cpu", "ram", "disk", "heartbeat", "recovery", "event_history", "profile", "market", "research")
        return RuntimeServiceReport(
            status=status,
            reason=reason,
            runtime_gate=gate,
            supervisor_status=supervisor_status,
            heartbeat_status=heartbeat_status,
            recovery_status=recovery.status,
            internet_status=internet_status,
            mt5_status=mt5_status,
            broker_status=broker_status,
            trading_status=recovery.trading_status,
            waiting_reason=recovery.waiting_reason,
            expected_next_action=recovery.expected_next_action,
            runtime_seconds=runtime_seconds,
            heartbeat_age_seconds=heartbeat_age,
            restart_count=restart_count,
            unexpected_exception_count=unexpected_exception_count,
            reconnect_count=reconnect_count,
            internet_disconnect_count=disconnect_count,
            internet_disconnect_duration_seconds=disconnect_duration,
            cpu_percent=cpu,
            ram_percent=ram,
            disk_percent=disk,
            event_history=event_history,
            dashboard_sections=sections,
        )

    def explain_one(self, record: Mapping[str, Any]) -> RuntimeServiceReport:
        return self.evaluate_one(record)
