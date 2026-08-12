"""Append-only A18 research progress observability; no scheduler or execution."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from afip.historical_replay_research import AppendOnlyResearchDataset

_STATUSES = {"RUNNING", "WAITING", "STALLED", "COMPLETED", "FAILED"}

def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

@dataclass(frozen=True)
class A18ResearchRuntimeStatus:
    research_run_id: str; status: str; progress_current: int; progress_total: int
    heartbeat_at_utc: str; reason_code: str; dataset_counts: Mapping[str, int]
    research_only: bool = True; execution_authority: str = "NONE"
    def __post_init__(self) -> None:
        if not self.research_run_id.strip() or self.status not in _STATUSES or not self.reason_code.strip():
            raise ValueError('A18 status is incomplete or invalid')
        if self.progress_current < 0 or self.progress_total < 0 or self.progress_current > self.progress_total:
            raise ValueError('A18 progress is invalid')
        if self.execution_authority != 'NONE' or not self.research_only:
            raise ValueError('A18 observability has no execution authority')
    @property
    def progress_ratio(self) -> float:
        return 0.0 if self.progress_total == 0 else self.progress_current / self.progress_total
    def as_dict(self) -> dict[str, Any]:
        value=asdict(self); value['progress_ratio']=self.progress_ratio; return value

class A18ResearchObservability:
    """Records honest research status; it never starts, stops, or schedules work."""
    def __init__(self, dataset: AppendOnlyResearchDataset) -> None: self.dataset=dataset
    def record(self, *, research_run_id: str, status: str, progress_current: int, progress_total: int, reason_code: str, heartbeat_at_utc: str | None = None) -> A18ResearchRuntimeStatus:
        item=A18ResearchRuntimeStatus(research_run_id, status, progress_current, progress_total, heartbeat_at_utc or _utc_now(), reason_code, {name:self.dataset.count(name) for name in self.dataset.DATASET_NAMES})
        self.dataset.append('a18_research_runtime_status', item.as_dict()); return item
    def latest(self) -> A18ResearchRuntimeStatus | None:
        records=self.dataset.records('a18_research_runtime_status')
        return None if not records else A18ResearchRuntimeStatus(**{key:value for key,value in records[-1]['record'].items() if key != 'progress_ratio'})
