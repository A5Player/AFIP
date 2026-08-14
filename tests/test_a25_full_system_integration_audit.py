import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('a25_audit',ROOT/'tools'/'afip_a25_full_system_integration_audit.py')
MODULE=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=MODULE;SPEC.loader.exec_module(MODULE)

def test_current_repository_passes_a25_integration_audit():
    report=MODULE.audit(ROOT)
    assert report['status']=='PASS',report['failed_checks']
    assert report['execution_authority_changed'] is False
    assert report['source_modified_by_audit'] is False
    assert report['automatic_repair_performed'] is False

def test_a25_covers_authority_data_dashboard_and_leakage_boundaries():
    report=MODULE.audit(ROOT)
    checks={item['check_id']:item['status'] for item in report['findings']}
    assert checks=={
      'SOURCE_TOPOLOGY':'PASS','SOURCE_PARSE':'PASS','RESEARCH_EXECUTION_ISOLATION':'PASS',
      'APPEND_ONLY_DATASET_CHAIN':'PASS','RESEARCH_PUBLIC_CONTRACT':'PASS',
      'READ_ONLY_DASHBOARD_CHAIN':'PASS','A24_DECISION_OUTCOME_SAFETY':'PASS',
      'A16_A24_TEST_CONTINUITY':'PASS'}
