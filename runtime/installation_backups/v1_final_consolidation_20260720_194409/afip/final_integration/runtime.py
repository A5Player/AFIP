from __future__ import annotations
from dataclasses import dataclass,asdict
import os,signal,subprocess,sys
from pathlib import Path
from typing import Any
from .architecture import ArchitectureRegistry
from .io import atomic_json,pid_running,read_json,utc_now
@dataclass(frozen=True)
class FinalIntegrationStatus:
 schema_version:str; status:str; updated_at_utc:str; trading_runtime:dict[str,Any]; research_runtime:dict[str,Any]; dashboard:dict[str,Any]; architecture:dict[str,Any]
 def as_dict(self)->dict[str,Any]:return asdict(self)
class FinalIntegrationRuntime:
 """Single operational authority. Trading and research remain isolated by design."""
 def __init__(self,root:str|Path='.') -> None:
  self.root=Path(root).resolve();self.control=self.root/'runtime/control/final_integration';self.logs=self.root/'runtime/logs';self.status_path=self.root/'runtime/final_integration_status.json';self.research_pid_path=self.control/'research_runtime.pid';self.stop_flag=self.control/'stop_research_runtime.flag'
 def _pid(self):
  try:return int(self.research_pid_path.read_text(encoding='utf-8').strip())
  except (OSError,ValueError):return None
 def _trading(self,command:str)->dict[str,Any]:
  try:
   cp=subprocess.run([sys.executable,'-m','tools.afip_demo_execution_control',command],cwd=self.root,text=True,capture_output=True,check=False)
   import json
   return json.loads(cp.stdout) if cp.stdout.strip() else {'status':'ERROR','returncode':cp.returncode,'stderr':cp.stderr[-1000:]}
  except Exception as exc:return {'status':'ERROR','reason':f'{type(exc).__name__}: {exc}'}
 def start(self)->FinalIntegrationStatus:
  self.control.mkdir(parents=True,exist_ok=True);self.logs.mkdir(parents=True,exist_ok=True);self.stop_flag.unlink(missing_ok=True)
  pid=self._pid()
  if not pid_running(pid):
   out=(self.logs/'afip_research_runtime.log').open('a',encoding='utf-8')
   proc=subprocess.Popen([sys.executable,'-m','tools.afip_final_integration','research-forever','--root',str(self.root)],cwd=self.root,stdout=out,stderr=subprocess.STDOUT)
   self.research_pid_path.write_text(str(proc.pid),encoding='utf-8')
  self._trading('start-all')
  from .dashboard import UnifiedDashboardAuthority
  UnifiedDashboardAuthority(self.root).build();return self.status()
 def stop(self)->FinalIntegrationStatus:
  self._trading('stop-all');self.stop_flag.parent.mkdir(parents=True,exist_ok=True);self.stop_flag.write_text(utc_now(),encoding='utf-8')
  pid=self._pid()
  if pid_running(pid):
   try:os.kill(pid,signal.SIGTERM)
   except OSError:pass
  self.research_pid_path.unlink(missing_ok=True);return self.status()
 def status(self)->FinalIntegrationStatus:
  trading=self._trading('status');pid=self._pid();research={'process_state':'RUNNING' if pid_running(pid) else 'STOPPED','pid':pid,'engine':read_json(self.root/'runtime/research/research_engine_status.json'),'file_index':read_json(self.root/'runtime/research/research_file_index.json'),'observatory':read_json(self.root/'runtime/research/runtime_observatory_status.json')}
  architecture=ArchitectureRegistry(self.root).inspect().as_dict();dashboard_path=self.root/'runtime/dashboard/afip_dashboard.html'
  active_trading=any(x.get('runtime_state')=='RUNNING' for x in trading.get('profiles',[]) if isinstance(x,dict));active_research=research['process_state']=='RUNNING';status='RUNNING' if active_trading or active_research else 'STOPPED'
  value=FinalIntegrationStatus('afip-final-integration.v2',status,utc_now(),trading,research,{'authority':'UNIFIED_DASHBOARD','path':'runtime/dashboard/afip_dashboard.html','exists':dashboard_path.exists()},architecture);atomic_json(self.status_path,value.as_dict());return value
