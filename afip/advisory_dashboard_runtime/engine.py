from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from afip.advisory_dashboard_adapter import AdvisoryDashboardPanelAdapter
from afip.advisory_dashboard_presentation import AdvisoryDashboardPresentationRuntime
from afip.advisory_dashboard_read_model import AdvisoryDashboardReadModelRuntime

RUNTIME_READY = "RUNTIME_READY"
RUNTIME_WAIT = "RUNTIME_WAIT"
RUNTIME_BLOCKED = "RUNTIME_BLOCKED"


@dataclass(frozen=True)
class AdvisoryDashboardRuntimeResult:
    status: str
    reason: str
    panel: Mapping[str, Any]
    source_path: str
    display_ready: bool
    execution_authority: bool = False
    order_send_called: bool = False
    order_modify_called: bool = False
    order_close_called: bool = False


class AdvisoryDashboardRuntime:
    """End-to-end read-only dashboard runtime for Milestone W advisory data."""

    def __init__(self, max_age_seconds: int = 300) -> None:
        self.reader = AdvisoryDashboardReadModelRuntime(max_age_seconds=max_age_seconds)
        self.presenter = AdvisoryDashboardPresentationRuntime()
        self.adapter = AdvisoryDashboardPanelAdapter()

    @staticmethod
    def _read_model_to_mapping(model: Any) -> dict[str, Any]:
        return asdict(model)

    @staticmethod
    def _presentation_to_mapping(model: Any) -> dict[str, Any]:
        data = asdict(model)
        data["stages"] = [asdict(stage) for stage in model.stages]
        return data

    def build_from_snapshot(
        self,
        snapshot_path: str | Path,
        now_utc=None,
    ) -> AdvisoryDashboardRuntimeResult:
        source = Path(snapshot_path)

        read_model = self.reader.load(source, now_utc=now_utc)
        read_mapping = self._read_model_to_mapping(read_model)

        presentation = self.presenter.build(read_mapping)
        presentation_mapping = self._presentation_to_mapping(presentation)

        panel = self.adapter.build(presentation_mapping)
        panel_mapping = self.adapter.to_dict(panel)

        if panel.adapter_status == "ADAPTER_READY" and panel.display_ready:
            status = RUNTIME_READY
            reason = "advisory_dashboard_runtime_ready"
        elif panel.adapter_status == "ADAPTER_WAIT":
            status = RUNTIME_WAIT
            reason = panel.reason or "advisory_dashboard_runtime_waiting"
        else:
            status = RUNTIME_BLOCKED
            reason = panel.reason or "advisory_dashboard_runtime_blocked"

        return AdvisoryDashboardRuntimeResult(
            status=status,
            reason=reason,
            panel=panel_mapping,
            source_path=str(source),
            display_ready=status == RUNTIME_READY,
        )

    @staticmethod
    def inject_into_dashboard_context(
        dashboard_context: Mapping[str, Any],
        runtime_result: AdvisoryDashboardRuntimeResult,
    ) -> dict[str, Any]:
        updated = dict(dashboard_context)
        updated["advisory_intelligence"] = dict(runtime_result.panel)
        updated["advisory_runtime_status"] = runtime_result.status
        updated["advisory_runtime_reason"] = runtime_result.reason
        updated["advisory_display_ready"] = runtime_result.display_ready
        return updated
