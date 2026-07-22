from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from typing import Any
from .io import atomic_json,utc_now

CANONICAL_ENTRY_POINTS=('START_AFIP.ps1','STOP_AFIP.ps1','STATUS_AFIP.ps1')
LEGACY_PATTERNS=('START_*.ps1','STOP_*.ps1','STATUS_*.ps1','RUN_*RESEARCH*.ps1','BUILD_*DASHBOARD*.ps1')
@dataclass(frozen=True)
class ArchitectureReport:
 schema_version:str; status:str; generated_at_utc:str; runtime_authorities:tuple[str,...]; dashboard_authority:str; data_lake_authority:str; incremental_index:str; canonical_entry_points:tuple[str,...]; compatibility_entry_points:tuple[str,...]; blockers:tuple[str,...]
 def as_dict(self)->dict[str,Any]:return asdict(self)
class ArchitectureRegistry:
 def __init__(self,root:str|Path='.') -> None:self.root=Path(root).resolve();self.path=self.root/'runtime/control/final_integration/architecture_registry.json'
 def inspect(self)->ArchitectureReport:
  legacy=set()
  for pattern in LEGACY_PATTERNS:
   for p in self.root.glob(pattern):
    if p.name not in CANONICAL_ENTRY_POINTS:legacy.add(p.name)
  blockers=[]
  required=('afip/final_integration/runtime.py','afip/final_integration/research_engine.py','afip/final_integration/dashboard.py','tools/afip_final_integration.py')
  for rel in required:
   if not (self.root/rel).is_file():blockers.append('missing:'+rel)
  report=ArchitectureReport('afip-final-architecture.v1','READY' if not blockers else 'BLOCKED',utc_now(),('TRADING_RUNTIME','RESEARCH_RUNTIME'),'runtime/dashboard/afip_dashboard.html','runtime/research/historical_data_lake','runtime/research/research_file_index.json',CANONICAL_ENTRY_POINTS,tuple(sorted(legacy)),tuple(blockers))
  atomic_json(self.path,report.as_dict());return report
