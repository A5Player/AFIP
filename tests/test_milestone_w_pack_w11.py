import json
from datetime import datetime,timezone
from afip.advisory_snapshot import AdvisorySnapshotExporter,SNAPSHOT_READY,SNAPSHOT_WAIT,SNAPSHOT_BLOCKED,SCHEMA_VERSION

def _cert(status="CERTIFIED"):
 return {"status":status,"snapshot_id":"AFIP-W10-ABC"}
def _trace(status="TRACE_COMPLETE"):
 return {"status":status,"trace_id":"AFIP-W9-XYZ","case_id":"case-1","stages":[{"stage":"CONTEXT","status":"PASS"}]}

def test_ready_snapshot_is_deterministic():
 e=AdvisorySnapshotExporter(); now=datetime(2026,7,30,tzinfo=timezone.utc)
 a=e.build(_cert(),_trace(),now); b=e.build(_cert(),_trace(),now)
 assert a.status==SNAPSHOT_READY and a.snapshot_id==b.snapshot_id and a.source_digest==b.source_digest

def test_incomplete_upstream_waits():
 assert AdvisorySnapshotExporter().build(_cert("REVIEW_REQUIRED"),_trace()).status==SNAPSHOT_WAIT

def test_blocked_upstream_blocks():
 assert AdvisorySnapshotExporter().build(_cert("BLOCKED"),_trace()).status==SNAPSHOT_BLOCKED
 assert AdvisorySnapshotExporter().build(_cert(),_trace("TRACE_BLOCKED")).status==SNAPSHOT_BLOCKED

def test_atomic_export_round_trip(tmp_path):
 e=AdvisorySnapshotExporter(); s=e.build(_cert(),_trace())
 target=e.export_atomic(s,tmp_path/"snapshot.json")
 data=json.loads(target.read_text(encoding="utf-8"))
 assert data["schema_version"]==SCHEMA_VERSION and data["snapshot_id"]==s.snapshot_id
 assert not list(tmp_path.glob("*.tmp"))

def test_no_execution_authority_and_contract():
 s=AdvisorySnapshotExporter().build(_cert(),_trace())
 assert s.execution_authority is False and s.order_send_called is False
 assert s.order_modify_called is False and s.order_close_called is False
 root=__import__("pathlib").Path(__file__).resolve().parents[1]
 c=json.loads((root/"config/advisory_snapshot_contract.json").read_text(encoding="utf-8"))
 assert c["write_policy"]=="ATOMIC_REPLACE" and c["fail_closed"] is True
