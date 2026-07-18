from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Mapping, Sequence
import json

@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id:str
    dataset_ids:tuple[str,...]
    code_version:str
    config_hash:str
    seed:int
    parameters:tuple[tuple[str,str],...]

    def canonical(self)->dict:
        return {"experiment_id":self.experiment_id,"dataset_ids":list(self.dataset_ids),"code_version":self.code_version,
                "config_hash":self.config_hash,"seed":self.seed,"parameters":[list(x) for x in self.parameters]}

class ExperimentReplayRegistry:
    def __init__(self, policy:Mapping[str,object]|None=None):
        self.policy=dict(policy or {})
        if self.policy.get("execution_authority","NONE")!="NONE": raise ValueError("execution_authority_must_be_none")
        if self.policy.get("live_execution","PROHIBITED")!="PROHIBITED": raise ValueError("live_execution_must_be_prohibited")

    def fingerprint(self,spec:ExperimentSpec)->str:
        raw=json.dumps(spec.canonical(),sort_keys=True,separators=(",",":")).encode()
        return "exp_"+sha256(raw).hexdigest()[:24]

    def build_replay_plan(self,spec:ExperimentSpec,available_datasets:Sequence[str])->dict:
        missing=sorted(set(spec.dataset_ids).difference(available_datasets))
        return {"fingerprint":self.fingerprint(spec),"experiment_id":spec.experiment_id,
                "status":"BLOCKED" if missing else "READY_FOR_REPLAY","missing_datasets":missing,
                "execution_mode":"OFFLINE_RESEARCH_ONLY","automatic_execution":False}

    @staticmethod
    def write_manifest(plan:dict,path:str|Path)->None:
        p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(plan,indent=2,sort_keys=True),encoding="utf-8")
