from pathlib import Path
import json
from afip.final_integration import ArchitectureRegistry,FinalIntegrationRuntime,UnifiedDashboardAuthority,UnifiedResearchEngine

def test_architecture_has_two_runtime_authorities(tmp_path):
 for rel in ('afip/final_integration/runtime.py','afip/final_integration/research_engine.py','afip/final_integration/dashboard.py','tools/afip_final_integration.py'):
  p=tmp_path/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('x',encoding='utf-8')
 report=ArchitectureRegistry(tmp_path).inspect();assert report.status=='READY';assert report.runtime_authorities==('TRADING_RUNTIME','RESEARCH_RUNTIME')
def test_research_has_no_execution_authority(tmp_path):
 status=UnifiedResearchEngine(tmp_path).status();assert status['live_execution_enabled'] is False;assert status['order_send_called'] is False
def test_dashboard_is_single_canonical_output(tmp_path,monkeypatch):
 monkeypatch.setattr(FinalIntegrationRuntime,'_trading',lambda self,cmd:{'status':'READY','profiles':[]})
 path=UnifiedDashboardAuthority(tmp_path).build();assert path==tmp_path/'runtime/dashboard/afip_dashboard.html';text=path.read_text(encoding='utf-8');assert 'Unified Dashboard' in text and 'Research Engine' in text
def test_status_is_atomic_and_machine_readable(tmp_path,monkeypatch):
 monkeypatch.setattr(FinalIntegrationRuntime,'_trading',lambda self,cmd:{'status':'READY','profiles':[]})
 value=FinalIntegrationRuntime(tmp_path).status();payload=json.loads((tmp_path/'runtime/final_integration_status.json').read_text());assert value.schema_version=='afip-final-integration.v2';assert payload['architecture']['runtime_authorities']==['TRADING_RUNTIME','RESEARCH_RUNTIME']
