from pathlib import Path
TEXT=(Path(__file__).resolve().parents[1]/'tools'/'afip_a27_active_readonly_demo_identity.py').read_text(encoding='utf-8')
def test_active_readonly_requires_explicit_approval_and_running_terminals():
 assert '--approve-active-readonly' in TEXT and 'passive_mapping_not_ready' in TEXT
 assert 'expected.issubset(running)' in TEXT
def test_active_identity_checks_demo_login_server_and_gold_without_orders():
 for marker in ('ACCOUNT_TRADE_MODE_DEMO','account_match','server_match','symbol_available','tick_available'):
  assert marker in TEXT
 assert 'mt5.order_send' not in TEXT and 'mt5.order_check' not in TEXT
 assert 'order_send_called":False' in TEXT and 'execution_authority":"NONE' in TEXT
