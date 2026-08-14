from pathlib import Path

def test_a27_preflight_is_passive_and_fail_closed():
 text=(Path(__file__).resolve().parents[1]/'tools'/'afip_a27_demo_readonly_preflight.py').read_text(encoding='utf-8')
 assert 'manager.check(active=False)' in text
 assert 'demo_identity_verified":False' in text
 assert 'orders_sent":False' in text and 'execution_authority":"NONE' in text
 assert 'MetaTrader5 as mt5' not in text and 'order_send(' not in text and 'initialize(' not in text

def test_a27_suppresses_existing_runtime_telemetry_writers():
 text=(Path(__file__).resolve().parents[1]/'tools'/'afip_a27_demo_readonly_preflight.py').read_text(encoding='utf-8')
 assert 'manager._write_health=lambda' in text
 assert 'manager._write_live_snapshot=lambda' in text
 assert 'runtime_telemetry_written":False' in text
