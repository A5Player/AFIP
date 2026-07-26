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
 def as_dict(self)->dict[str,Any]:
  data=asdict(self);data['architecture']['runtime_authorities']=list(data['architecture'].get('runtime_authorities',()));data['historical_data_lake']=data['architecture'].get('historical_data_lake',{'incremental_index':'runtime/research/research_file_index.json','execution_authority':False});return data
class FinalIntegrationRuntime:
 """Single operational authority. Trading, research and dashboard are isolated processes."""
 def __init__(self,root:str|Path='.') -> None:
  self.root=Path(root).resolve();self.control=self.root/'runtime/control/final_integration';self.logs=self.root/'runtime/logs';self.status_path=self.root/'runtime/final_integration_status.json';self.research_pid_path=self.control/'research_runtime.pid';self.dashboard_pid_path=self.control/'dashboard_monitor.pid';self.stop_flag=self.control/'stop_research_runtime.flag'
 def _pid(self,path:Path):
  try:return int(path.read_text(encoding='utf-8').strip())
  except (OSError,ValueError):return None
 def _trading(self,command:str)->dict[str,Any]:
  try:
   cp=subprocess.run([sys.executable,'-m','tools.afip_demo_execution_control',command],cwd=self.root,text=True,capture_output=True,check=False)
   import json
   return json.loads(cp.stdout) if cp.stdout.strip() else {'status':'ERROR','returncode':cp.returncode,'stderr':cp.stderr[-2000:]}
  except Exception as exc:return {'status':'ERROR','reason':f'{type(exc).__name__}: {exc}'}
 def _spawn(self,pid_path:Path,command:list[str],log_name:str)->None:
  pid=self._pid(pid_path)
  if pid_running(pid): return
  out=(self.logs/log_name).open('a',encoding='utf-8')
  kwargs:dict[str,Any]={'cwd':self.root,'stdout':out,'stderr':subprocess.STDOUT}
  if os.name=='nt':
   kwargs['creationflags']=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)|getattr(subprocess,'DETACHED_PROCESS',0)
  else:
   kwargs['start_new_session']=True
  proc=subprocess.Popen(command,**kwargs)
  out.close()
  pid_path.write_text(str(proc.pid),encoding='utf-8')
 def start(self)->FinalIntegrationStatus:
  self.control.mkdir(parents=True,exist_ok=True);self.logs.mkdir(parents=True,exist_ok=True);self.stop_flag.unlink(missing_ok=True)
  self._spawn(self.research_pid_path,[sys.executable,'-m','tools.afip_final_integration','research-forever','--root',str(self.root)],'afip_research_runtime.log')
  self._spawn(self.dashboard_pid_path,[sys.executable,'-m','tools.afip_dashboard_monitor','--root',str(self.root),'--fast-interval','10','--full-interval','60'],'afip_dashboard_monitor.log')
  trading=self._trading('start-all')
  if trading.get('status')=='BLOCKED': return self.status()
  from .dashboard import UnifiedDashboardAuthority
  UnifiedDashboardAuthority(self.root).build();return self.status()
 def _write_stopped_snapshot(self,path:Path,**values:Any)->None:
  previous=read_json(path);now=utc_now();atomic_json(path,{**previous,**values,'status':'STOPPED','updated_at_utc':now,'heartbeat_utc':now,'pid':None,'process_id':None,'execution_authority':False,'order_send_called':False})
 def stop(self)->FinalIntegrationStatus:
  self._trading('stop-all');self.stop_flag.parent.mkdir(parents=True,exist_ok=True);self.stop_flag.write_text(utc_now(),encoding='utf-8')
  for path in (self.research_pid_path,self.dashboard_pid_path):
   pid=self._pid(path)
   if pid_running(pid):
    try:os.kill(pid,signal.SIGTERM)
    except OSError:pass
   path.unlink(missing_ok=True)
  self._write_stopped_snapshot(self.root/'runtime/research/research_engine_status.json',live_execution_enabled=False)
  self._write_stopped_snapshot(self.root/'runtime/research/runtime_observatory_status.json',stage='STOPPED',current_activity='Research runtime stopped')
  self._write_stopped_snapshot(self.root/'runtime/dashboard/dashboard_monitor_status.json',cycles=read_json(self.root/'runtime/dashboard/dashboard_monitor_status.json').get('cycles',0),execution_authority=False)
  return self.status()
 def status(self)->FinalIntegrationStatus:
  trading=self._trading('status');rpid=self._pid(self.research_pid_path);dpid=self._pid(self.dashboard_pid_path)
  research_running=pid_running(rpid);engine=read_json(self.root/'runtime/research/research_engine_status.json');observatory=read_json(self.root/'runtime/research/runtime_observatory_status.json')
  if not research_running:
   engine={**engine,'status':'STOPPED','pid':None,'process_id':None,'live_execution_enabled':False,'order_send_called':False}
   observatory={**observatory,'status':'STOPPED','stage':'STOPPED','current_activity':'Research runtime stopped','pid':None,'process_id':None,'execution_authority':False,'order_send_called':False}
  research={'process_state':'RUNNING' if research_running else 'STOPPED','pid':rpid if research_running else None,'engine':engine,'file_index':read_json(self.root/'runtime/research/research_file_index.json'),'observatory':observatory,'blocks_trading_start':False}
  architecture=ArchitectureRegistry(self.root).inspect().as_dict();architecture['runtime_authorities']=list(architecture.get('runtime_authorities', ()));architecture['execution_authority_in_research']=False;dashboard_path=self.root/'runtime/dashboard/afip_dashboard.html'
  dashboard_running=pid_running(dpid);dashboard_status=read_json(self.root/'runtime/dashboard/dashboard_monitor_status.json')
  if not dashboard_running: dashboard_status={**dashboard_status,'status':'STOPPED','pid':None,'process_id':None,'execution_authority':False}
  dashboard={'authority':'AFIP_SINGLE_PRODUCTION_DASHBOARD','path':'runtime/dashboard/afip_dashboard.html','exists':dashboard_path.exists(),'process_state':'RUNNING' if dashboard_running else 'STOPPED','pid':dpid if dashboard_running else None,'refresh_interval_seconds':10,'fast_refresh_interval_seconds':10,'full_refresh_interval_seconds':60,'background_only':True,'execution_authority':False,'status':dashboard_status}
  router=trading.get('router') if isinstance(trading.get('router'),dict) else None
  if router is not None and not router.get('running'):
   trading={**trading,'router':{**router,'pid':None,'state':'STOPPED','running':False}}
  active_trading=any(x.get('runtime_state')=='RUNNING' for x in trading.get('profiles',[]) if isinstance(x,dict));active_research=research['process_state']=='RUNNING';status='RUNNING' if active_trading or active_research else 'STOPPED'
  historical_data_lake={'incremental_index':'runtime/research/research_file_index.json','execution_authority':False};architecture['historical_data_lake']=historical_data_lake;value=FinalIntegrationStatus('afip-final-integration.v4',status,utc_now(),trading,research,dashboard,architecture);payload=value.as_dict();payload['historical_data_lake']=historical_data_lake;atomic_json(self.status_path,payload);return value
