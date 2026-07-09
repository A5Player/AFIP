"""Dashboard Runtime status composer for Milestone H Pack 3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from afip.connection_manager import ConnectionManagerRuntime
from afip.historical_data_manager import HistoricalDataDownloadPipeline, HistoricalDataManagerRuntime
from afip.profile_manager import ProfileManagerRuntime
from afip.runtime_service_manager import RuntimeServiceManager
from afip.setup_wizard import SetupWizardRuntime


@dataclass(frozen=True)
class DashboardRuntimeStatusReport:
    status: str
    reason: str
    dashboard_runtime_gate: str
    profile_status: str
    setup_status: str
    connection_status: str
    historical_data_status: str
    runtime_service_status: str
    historical_download_status: str
    order_center_sections: tuple[str, ...]
    dashboard_sections: tuple[str, ...]
    decision_explainability_sections: tuple[str, ...]
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        return (
            "AFIP Dashboard Runtime\n"
            f"Status: {self.status}\n"
            f"Gate: {self.dashboard_runtime_gate}\n"
            f"Reason: {self.reason}\n"
            f"Profile: {self.profile_status}\n"
            f"Setup: {self.setup_status}\n"
            f"Connection: {self.connection_status}\n"
            f"Historical Data: {self.historical_data_status}"
            f"\nRuntime Service: {self.runtime_service_status}"
            f"\nHistorical Download: {self.historical_download_status}"
        )


class DashboardRuntimeStatus:
    """Compose dashboard runtime readiness across H Pack 3 managers."""

    def evaluate_one(self, record: Mapping[str, Any]) -> DashboardRuntimeStatusReport:
        profile = ProfileManagerRuntime().evaluate_one(record)
        setup = SetupWizardRuntime().evaluate_one(record)
        connection = ConnectionManagerRuntime().evaluate_one(record)
        history = HistoricalDataManagerRuntime().evaluate_one(record)
        runtime_service = RuntimeServiceManager().evaluate_one(record)
        historical_download = HistoricalDataDownloadPipeline().evaluate_one(record)
        sections = ("runtime", "intelligence", "engine", "trading", "analytics", "afip_bank", "research", "system", "market")
        order_sections = ("waiting", "reason", "ready", "opened", "managing", "closing", "closed", "close_reason", "order_quality")
        explainability = ("waiting", "entry", "holding", "trailing_stop", "break_even", "stop_loss_move", "partial_close", "final_close", "rejected_entry", "rejected_exit", "alternative_decision", "current_ai_reasoning")
        statuses = (profile.status, setup.status, connection.status, history.status, runtime_service.status, historical_download.status)
        if "BLOCKED" in statuses:
            status, reason, gate = "BLOCKED", "dashboard_runtime_blocked_by_dependency", "BLOCKED"
        elif any(item in {"WAITING", "REVIEW", "RECOVERING"} for item in statuses):
            status, reason, gate = "WAITING", "dashboard_runtime_waiting_for_dependency", "WAITING"
        else:
            status, reason, gate = "READY", "dashboard_runtime_ready", "DASHBOARD_RUNTIME_READY"
        return DashboardRuntimeStatusReport(status, reason, gate, profile.status, setup.status, connection.status, history.status, runtime_service.status, historical_download.status, order_sections, sections, explainability)

    def explain_one(self, record: Mapping[str, Any]) -> DashboardRuntimeStatusReport:
        return self.evaluate_one(record)
