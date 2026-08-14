from pathlib import Path
TEXT=(Path(__file__).resolve().parents[1]/'tools'/'afip_a27_p4_demo_open_only_proof.py').read_text(encoding='utf-8')
def test_open_proof_uses_single_existing_gateway_and_p4_only():
 assert 'DemoExecutionGateway(profile,policy,mt5=guarded).run_cycle()' in TEXT
 assert 'DemoExecutionRunner._load(config,"P4")' in TEXT and 'AFIP_P4_DEMO_ARMED":"YES"' in TEXT
 assert 'AFIP_P1_DEMO_ARMED":"NO"' in TEXT and 'maximum_authorized_orders":1' in TEXT
def test_guard_requires_exact_volume_sl_tp_and_blocks_second_request():
 for marker in ('a27_volume_must_equal_0_01','a27_sl_tp_required','a27_exactly_one_order_guard','a27_unchecked_or_multiple_send_blocked'):
  assert marker in TEXT
def test_proof_has_no_automatic_close_path():
 assert 'automatic_close_performed":False' in TEXT and 'manual_close_required' in TEXT
 assert 'TRADE_ACTION_SLTP' not in TEXT and 'position_close' not in TEXT
