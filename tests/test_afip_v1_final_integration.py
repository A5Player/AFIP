from pathlib import Path
import json
from afip.final_integration import FinalIntegrationRuntime, UnifiedDashboardAuthority

def test_two_runtime_architecture_and_no_research_execution_authority(tmp_path:Path):
 s=FinalIntegrationRuntime(tmp_path).status().as_dict()
 assert s['architecture']['runtime_authorities']==['TRADING_RUNTIME','RESEARCH_RUNTIME']
 assert s['architecture']['execution_authority_in_research'] is False

def test_unified_dashboard_is_single_html_authority(tmp_path:Path):
 p=UnifiedDashboardAuthority(tmp_path).build()
 text=p.read_text(encoding='utf-8')
 assert p.name=='afip_dashboard.html'
 for name in ('Main','Intelligence &amp; Engine','Research','Profiles','Operations','Cross Market'): assert name in text

def test_incremental_index_contract_is_canonical(tmp_path:Path):
 s=FinalIntegrationRuntime(tmp_path).status().as_dict()
 assert s['historical_data_lake']['incremental_index']=='runtime/research/research_file_index.json'

def test_status_is_atomic_and_machine_readable(tmp_path:Path):
 r=FinalIntegrationRuntime(tmp_path); r.status(); value=json.loads(r.status_path.read_text(encoding='utf-8'))
 assert value['schema_version']=='afip-final-integration.v4'
