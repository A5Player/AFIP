from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Mapping
import json

@dataclass(frozen=True)
class FoundationCertification:
    certification_id:str
    status:str
    passed_checks:tuple[str,...]
    failed_checks:tuple[str,...]
    execution_authority:str="NONE"
    automatic_promotion:str="PROHIBITED"
    def to_dict(self): return asdict(self)

class DataFoundationCertifier:
    REQUIRED=("catalog","integrity","quality","retention","replay","usage","portability","certification")
    def __init__(self,policy:Mapping[str,object]|None=None):
        self.policy=dict(policy or {})
        if self.policy.get("execution_authority","NONE")!="NONE": raise ValueError("execution_authority_must_be_none")
        if self.policy.get("automatic_promotion","PROHIBITED")!="PROHIBITED": raise ValueError("automatic_promotion_must_be_prohibited")
    def certify(self,checks:Mapping[str,bool])->FoundationCertification:
        passed=tuple(sorted(k for k in self.REQUIRED if checks.get(k) is True))
        failed=tuple(sorted(k for k in self.REQUIRED if checks.get(k) is not True))
        status="CERTIFIED_RESEARCH_FOUNDATION" if not failed else "NOT_CERTIFIED"
        raw=json.dumps({"passed":passed,"failed":failed},sort_keys=True,separators=(",",":")).encode()
        cid="fdc_"+sha256(raw).hexdigest()[:24]
        return FoundationCertification(cid,status,passed,failed)
    @staticmethod
    def write_report(result:FoundationCertification,path:str|Path):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result.to_dict(),indent=2,sort_keys=True),encoding="utf-8")
