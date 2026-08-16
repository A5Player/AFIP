from __future__ import annotations
from pathlib import Path
from typing import Any
from .io import atomic_json,read_json,utc_now

class UnifiedResearchEngine:
    """Canonical research authority; continuous service, never execution authority."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()
        self.status_path = self.root / "runtime/research/research_engine_status.json"

    def _write(self, **values: Any) -> dict[str, Any]:
        previous = read_json(self.status_path)
        payload = {
            **previous,
            "schema_version": "afip-research-engine.v1",
            "status": "RUNNING",
            "service_state": "RUNNING",
            "live_execution_enabled": False,
            "execution_authority": False,
            "order_send_called": False,
            "heartbeat_utc": utc_now(),
            **values,
        }
        atomic_json(self.status_path, payload)
        return payload

    def mark_service_running(self, *, pid: int | None = None, cycles: int = 0) -> dict[str, Any]:
        return self._write(pid=pid, process_id=pid, cycles=cycles, current_activity="Research service waiting for next cycle")

    def run_once(self) -> dict[str, Any]:
        started = utc_now()
        self._write(started_at_utc=started, cycle_status="RUNNING", current_activity="Research cycle running")
        try:
            from afip.phase_v_major import PhaseVMajorRuntime
            result = PhaseVMajorRuntime(self.root).run_once()
            result = result.as_dict() if hasattr(result, "as_dict") else dict(result)
            from .continuous_research import ContinuousResearchPipeline
            continuous = ContinuousResearchPipeline(self.root).run_once()
            return self._write(
                cycle_status="READY",
                reason="research_cycle_complete",
                current_activity="Research cycle complete; service remains active",
                phase_v=result,
                a37_continuous_research=continuous,
                updated_at_utc=utc_now(),
            )
        except Exception as exc:
            return self._write(
                cycle_status="ERROR",
                reason=f"{type(exc).__name__}: {exc}",
                current_activity="Research cycle failed; service remains active",
                updated_at_utc=utc_now(),
            )

    def status(self) -> dict[str, Any]:
        value = read_json(self.status_path)
        return value or {
            "schema_version": "afip-research-engine.v1",
            "status": "NOT_STARTED",
            "service_state": "STOPPED",
            "live_execution_enabled": False,
            "execution_authority": False,
            "order_send_called": False,
        }
