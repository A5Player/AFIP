from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .engine import AdvisoryDashboardRuntime


DEFAULT_SNAPSHOT_PATH = Path("runtime/advisory_snapshot/advisory_runtime_snapshot.json")


def build_advisory_dashboard_context(
    project_root: str | Path,
    dashboard_context: Mapping[str, Any] | None = None,
    max_age_seconds: int = 300,
    now_utc=None,
) -> dict[str, Any]:
    """Build advisory dashboard context without mutating execution state."""
    root = Path(project_root)
    source = root / DEFAULT_SNAPSHOT_PATH
    runtime = AdvisoryDashboardRuntime(max_age_seconds=max_age_seconds)
    result = runtime.build_from_snapshot(source, now_utc=now_utc)
    return runtime.inject_into_dashboard_context(dashboard_context or {}, result)
