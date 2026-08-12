from pathlib import Path
import pytest
from afip.exit_evidence_research import A18ResearchObservability
from afip.historical_replay_research import AppendOnlyResearchDataset
def test_records_append_only_status_and_reads_latest(tmp_path: Path):
 d=AppendOnlyResearchDataset(tmp_path); o=A18ResearchObservability(d)
 item=o.record(research_run_id='A17-1',status='RUNNING',progress_current=2,progress_total=5,reason_code='replay_in_progress',heartbeat_at_utc='2026-01-01T00:00:00Z')
 assert item.progress_ratio == .4 and o.latest().status == 'RUNNING' and d.verify('a18_research_runtime_status')
def test_rejects_invalid_progress(tmp_path: Path):
 with pytest.raises(ValueError,match='progress'): A18ResearchObservability(AppendOnlyResearchDataset(tmp_path)).record(research_run_id='X',status='RUNNING',progress_current=2,progress_total=1,reason_code='bad')
