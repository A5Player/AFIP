"""Runtime recovery flow for safe VPS operation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

_SAFE_EXECUTION_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}


@dataclass(frozen=True)
class RuntimeRecoveryReport:
    status: str
    reason: str
    recovery_steps: tuple[str, ...]
    trading_status: str
    waiting_reason: str
    expected_next_action: str
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeRecoveryEngine:
    """Explain recovery steps before any trading resume decision."""

    def evaluate_one(self, record: Mapping[str, Any]) -> RuntimeRecoveryReport:
        execution_mode = str(record.get("execution_mode", "LOCKED_SIMULATION_ONLY")).strip().upper()
        internet_status = str(record.get("internet_status", "CONNECTED")).strip().upper()
        mt5_status = str(record.get("mt5_status", "CONNECTED")).strip().upper()
        broker_status = str(record.get("broker_status", "XM_READY")).strip().upper()
        steps: list[str] = []
        if execution_mode not in _SAFE_EXECUTION_MODES:
            return RuntimeRecoveryReport("BLOCKED", "live_execution_not_allowed_for_runtime_service", ("pause_trading", "require_safe_execution_mode"), "PAUSED", "safe_execution_mode_required", "switch_to_simulation_or_paper")
        if internet_status != "CONNECTED":
            steps.extend(("pause_trading", "wait_for_internet", "recheck_mt5", "recheck_broker"))
            return RuntimeRecoveryReport("RECOVERING", "internet_recovery_required", tuple(steps), "PAUSED", "internet_disconnected", "wait_for_internet_reconnect")
        if mt5_status != "CONNECTED":
            steps.extend(("pause_trading", "reconnect_mt5", "validate_broker", "resume_runtime_after_validation"))
            return RuntimeRecoveryReport("RECOVERING", "mt5_recovery_required", tuple(steps), "PAUSED", "mt5_not_connected", "reconnect_mt5")
        if broker_status not in {"XM_READY", "CONNECTED", "READY"}:
            steps.extend(("pause_trading", "validate_xm_broker", "refresh_connection_status", "resume_runtime_after_validation"))
            return RuntimeRecoveryReport("RECOVERING", "broker_recovery_required", tuple(steps), "PAUSED", "broker_not_ready", "validate_broker_connection")
        return RuntimeRecoveryReport("READY", "recovery_not_required", ("observe_runtime", "maintain_heartbeat"), "RUNNING", "-", "continue_runtime")

    def explain_one(self, record: Mapping[str, Any]) -> RuntimeRecoveryReport:
        return self.evaluate_one(record)
