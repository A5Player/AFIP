from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

@dataclass(frozen=True)
class UsageEvent:
    event_id:str
    dataset_id:str
    purpose:str
    consumer:str
    experiment_id:str|None
    evidence_refs:tuple[str,...]
    allowed:bool
    reason:str
    recorded_at:str
    execution_authority:str="NONE"
    def to_dict(self): return asdict(self)

class DatasetUsageLedger:
    def __init__(self,execution_authority:str="NONE"):
        if execution_authority!="NONE": raise ValueError("execution_authority_must_be_none")
    def record(self,dataset_id:str,purpose:str,consumer:str,readiness_level:str,
               evidence_refs:tuple[str,...]=(),experiment_id:str|None=None)->UsageEvent:
        allowed=readiness_level in {"RESEARCH_READY","CONDITIONALLY_READY"}
        reason="research_use_allowed" if allowed else "dataset_not_ready"
        raw=f"{dataset_id}|{purpose}|{consumer}|{readiness_level}|{experiment_id}|{sorted(evidence_refs)}"
        eid="use_"+sha256(raw.encode()).hexdigest()[:24]
        return UsageEvent(eid,dataset_id,purpose,consumer,experiment_id,tuple(sorted(evidence_refs)),allowed,reason,datetime.now(timezone.utc).isoformat())
    @staticmethod
    def append(event:UsageEvent,path:str|Path):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("a",encoding="utf-8",newline="\n") as h:
            h.write(json.dumps(event.to_dict(),sort_keys=True,separators=(",",":"))+"\n")
