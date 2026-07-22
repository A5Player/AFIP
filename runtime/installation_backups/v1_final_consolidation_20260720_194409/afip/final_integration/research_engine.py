from __future__ import annotations
from pathlib import Path
from typing import Any
from .io import atomic_json,read_json,utc_now
class UnifiedResearchEngine:
 """Canonical research authority delegating to existing Phase V and Automatic Research implementations."""
 def __init__(self,root:str|Path='.') -> None:
  self.root=Path(root).resolve();self.status_path=self.root/'runtime/research/research_engine_status.json'
 def run_once(self)->dict[str,Any]:
  started=utc_now(); payload={'schema_version':'afip-research-engine.v1','status':'RUNNING','started_at_utc':started,'live_execution_enabled':False,'order_send_called':False}
  atomic_json(self.status_path,payload)
  try:
   from afip.phase_v_major import PhaseVMajorRuntime
   result=PhaseVMajorRuntime(self.root).run_once()
   result=result.as_dict() if hasattr(result,'as_dict') else dict(result)
   payload.update(status='READY',reason='research_cycle_complete',phase_v=result)
  except Exception as exc:
   payload.update(status='ERROR',reason=f'{type(exc).__name__}: {exc}')
  payload['updated_at_utc']=utc_now();atomic_json(self.status_path,payload);return payload
 def status(self)->dict[str,Any]:
  value=read_json(self.status_path)
  return value or {'schema_version':'afip-research-engine.v1','status':'NOT_STARTED','live_execution_enabled':False,'order_send_called':False}
