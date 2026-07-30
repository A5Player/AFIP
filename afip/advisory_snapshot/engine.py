from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib, json, os, tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

SNAPSHOT_READY="SNAPSHOT_READY"
SNAPSHOT_WAIT="SNAPSHOT_WAIT"
SNAPSHOT_BLOCKED="SNAPSHOT_BLOCKED"
SCHEMA_VERSION="AFIP_ADVISORY_SNAPSHOT_V1"

@dataclass(frozen=True)
class AdvisorySnapshot:
    schema_version: str
    snapshot_id: str
    status: str
    reason: str
    generated_at_utc: str
    certification_status: str
    certification_snapshot_id: str
    trace_status: str
    trace_id: str
    case_id: str
    stage_summary: Sequence[Mapping[str, Any]]
    freshness_seconds: int
    source_digest: str
    execution_authority: bool=False
    order_send_called: bool=False
    order_modify_called: bool=False
    order_close_called: bool=False

class AdvisorySnapshotExporter:
    def build(self, certification: Mapping[str,Any], trace: Mapping[str,Any],
              now_utc: datetime|None=None) -> AdvisorySnapshot:
        now=now_utc or datetime.now(timezone.utc)
        cert_status=str(certification.get("status",""))
        trace_status=str(trace.get("status",""))
        stages=tuple(trace.get("stages",()) or ())
        if not cert_status or not trace_status:
            status,reason=SNAPSHOT_WAIT,"source_status_missing"
        elif cert_status=="BLOCKED" or trace_status=="TRACE_BLOCKED":
            status,reason=SNAPSHOT_BLOCKED,"upstream_blocked"
        elif cert_status!="CERTIFIED" or trace_status!="TRACE_COMPLETE":
            status,reason=SNAPSHOT_WAIT,"upstream_not_complete"
        else:
            status,reason=SNAPSHOT_READY,"advisory_snapshot_ready"
        canonical={
            "certification_snapshot_id":str(certification.get("snapshot_id","")),
            "certification_status":cert_status,
            "trace_id":str(trace.get("trace_id","")),
            "trace_status":trace_status,
            "case_id":str(trace.get("case_id","")),
            "stages":stages,
        }
        digest=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
        generated=now.astimezone(timezone.utc).isoformat()
        return AdvisorySnapshot(
            schema_version=SCHEMA_VERSION,
            snapshot_id=f"AFIP-W11-{digest[:16].upper()}",
            status=status,reason=reason,generated_at_utc=generated,
            certification_status=cert_status,
            certification_snapshot_id=canonical["certification_snapshot_id"],
            trace_status=trace_status,trace_id=canonical["trace_id"],
            case_id=canonical["case_id"],stage_summary=stages,
            freshness_seconds=0,source_digest=digest,
        )

    def export_atomic(self,snapshot:AdvisorySnapshot,target: str|Path)->Path:
        target=Path(target)
        target.parent.mkdir(parents=True,exist_ok=True)
        data=json.dumps(asdict(snapshot),indent=2,sort_keys=True,default=str)+"\n"
        fd,tmp=tempfile.mkstemp(prefix=target.name+".",suffix=".tmp",dir=str(target.parent))
        try:
            with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as handle:
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
        return target
