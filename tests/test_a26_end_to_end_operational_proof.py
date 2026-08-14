import importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('a26_proof',ROOT/'tools'/'afip_a26_end_to_end_operational_proof.py')
MODULE=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=MODULE;SPEC.loader.exec_module(MODULE)

def test_internal_end_to_end_chain_has_source_and_regression_evidence():
 report=MODULE.build_proof(ROOT)
 assert report['status']=='PASS_WITH_EXTERNAL_PROOF_REQUIRED',report['internal_failed_stages']
 assert all(item['status']=='TESTED' for item in report['stages'][:9])

def test_a26_never_claims_offline_proof_is_live_certification():
 report=MODULE.build_proof(ROOT);statuses={item['stage_id']:item['status'] for item in report['stages']}
 assert statuses['MT5_TERMINAL_BINDING']=='DEMO_PROOF_REQUIRED'
 assert statuses['BROKER_ORDER_LIFECYCLE']=='DEMO_PROOF_REQUIRED'
 assert statuses['LIVE_SLIPPAGE_AND_FILL']=='LIVE_PROOF_REQUIRED'
 assert statuses['LIVE_PROFITABILITY']=='LIVE_PROOF_REQUIRED'
 assert report['live_trading_certified'] is False and report['profitability_certified'] is False

def test_a26_is_observation_only_and_sends_no_orders():
 report=MODULE.build_proof(ROOT)
 assert report['orders_sent'] is False and report['mt5_imported'] is False and report['source_modified'] is False
 assert all(item['execution_performed'] is False for item in report['stages'])
