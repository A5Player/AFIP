from __future__ import annotations
import json, os
from pathlib import Path
from types import SimpleNamespace

from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager

class FakeMT5:
    def __init__(self, ok=True, login=101, server="XMGlobal-MT5 6", connected=True):
        self.ok=ok; self.login=login; self.server=server; self.connected=connected; self.calls=[]
    def initialize(self, **kwargs): self.calls.append(kwargs); return self.ok
    def shutdown(self): return None
    def account_info(self): return SimpleNamespace(login=self.login, server=self.server) if self.ok else None
    def terminal_info(self): return SimpleNamespace(connected=self.connected)
    def symbol_select(self, symbol, enable): return symbol == "GOLD#" and enable
    def symbol_info_tick(self, symbol): return SimpleNamespace(bid=1.0, ask=1.1) if symbol == "GOLD#" else None
    def last_error(self): return (1, "initialize_failed")

def config(tmp_path: Path, enabled=True):
    terminal=tmp_path/'P1'/'terminal64.exe'; terminal.parent.mkdir(); terminal.write_text('x')
    payload={"profiles":[]}
    for n in range(1,5):
        root=tmp_path/f'runtime/p{n}'
        payload['profiles'].append({
            "profile_id":f"P{n}","profile_name":f"Profile {n}","enabled": enabled if n==1 else False,
            "launch_mt5":False,"mt5_folder":str(tmp_path/f'P{n}'),"mt5_terminal":str(terminal if n==1 else tmp_path/f'P{n}/terminal64.exe'),
            "broker":"XM","server":"XMGlobal-MT5 6","symbol":"GOLD#","login_env":f"T_P{n}_LOGIN","password_env":f"T_P{n}_PASSWORD",
            "runtime_directory":str(root),"database_path":str(root/'db/a.sqlite3'),"logs_directory":str(root/'logs'),
            "dashboard_path":str(root/'dashboard/a.html'),"learning_directory":str(root/'learning'),"knowledge_directory":str(root/'knowledge'),
            "statistics_directory":str(root/'statistics'),"execution":"LOCKED_SIMULATION_ONLY","direct_execution":False,"live_execution":False})
    path=tmp_path/'config.json'; path.write_text(json.dumps(payload)); return path

def test_connected_profile_uses_exact_terminal_login_server_and_gold(tmp_path, monkeypatch):
    path=config(tmp_path); monkeypatch.setenv('T_P1_LOGIN','101'); monkeypatch.setenv('T_P1_PASSWORD','secret')
    fake=FakeMT5(); report=MT5MultiTerminalConnectionManager(path, lambda: fake).check(['P1'])
    item=report['profiles'][0]
    assert item['connection_status']=='CONNECTED' and item['symbol_available'] and item['tick_available']
    assert fake.calls[0]['path'].endswith('terminal64.exe') and fake.calls[0]['login']==101
    assert fake.calls[0]['server']=='XMGlobal-MT5 6' and fake.calls[0]['portable'] is True
    assert item['execution']=='LOCKED_SIMULATION_ONLY' and item['order_status']=='NO_ORDER_SENT'

def test_missing_terminal_is_blocked_without_adapter(tmp_path, monkeypatch):
    path=config(tmp_path); data=json.loads(path.read_text()); data['profiles'][0]['mt5_terminal']=str(tmp_path/'missing.exe'); path.write_text(json.dumps(data))
    monkeypatch.setenv('T_P1_LOGIN','101'); monkeypatch.setenv('T_P1_PASSWORD','secret')
    item=MT5MultiTerminalConnectionManager(path, lambda: (_ for _ in ()).throw(AssertionError())).check(['P1'])['profiles'][0]
    assert item['connection_status']=='BLOCKED' and 'not found' in item['reason']

def test_missing_credentials_is_blocked(tmp_path, monkeypatch):
    path=config(tmp_path); monkeypatch.delenv('T_P1_LOGIN',raising=False); monkeypatch.delenv('T_P1_PASSWORD',raising=False)
    item=MT5MultiTerminalConnectionManager(path, lambda: FakeMT5()).check(['P1'])['profiles'][0]
    assert item['connection_status']=='BLOCKED' and item['account']=='NOT_CONFIGURED'

def test_account_mismatch_is_degraded_and_masked(tmp_path, monkeypatch):
    path=config(tmp_path); monkeypatch.setenv('T_P1_LOGIN','101'); monkeypatch.setenv('T_P1_PASSWORD','secret')
    item=MT5MultiTerminalConnectionManager(path, lambda: FakeMT5(login=202)).check(['P1'])['profiles'][0]
    assert item['connection_status']=='DEGRADED' and not item['account_match'] and item['account']=='****202'

def test_server_mismatch_is_degraded(tmp_path, monkeypatch):
    path=config(tmp_path); monkeypatch.setenv('T_P1_LOGIN','101'); monkeypatch.setenv('T_P1_PASSWORD','secret')
    item=MT5MultiTerminalConnectionManager(path, lambda: FakeMT5(server='OTHER')).check(['P1'])['profiles'][0]
    assert item['connection_status']=='DEGRADED' and not item['server_match']

def test_initialize_failure_is_disconnected_and_retried(tmp_path, monkeypatch):
    path=config(tmp_path); monkeypatch.setenv('T_P1_LOGIN','101'); monkeypatch.setenv('T_P1_PASSWORD','secret')
    fake=FakeMT5(ok=False); item=MT5MultiTerminalConnectionManager(path, lambda: fake).check(['P1'], reconnect_attempts=2)['profiles'][0]
    assert item['connection_status']=='DISCONNECTED' and len(fake.calls)==3 and item['reconnect_attempts']==2

def test_disabled_profile_never_initializes(tmp_path):
    path=config(tmp_path, enabled=False)
    item=MT5MultiTerminalConnectionManager(path, lambda: (_ for _ in ()).throw(AssertionError())).check(['P1'])['profiles'][0]
    assert item['connection_status']=='STOPPED'

def test_health_snapshot_is_written_per_profile(tmp_path, monkeypatch):
    path=config(tmp_path); monkeypatch.setenv('T_P1_LOGIN','101'); monkeypatch.setenv('T_P1_PASSWORD','secret')
    item=MT5MultiTerminalConnectionManager(path, lambda: FakeMT5()).check(['P1'])['profiles'][0]
    health=Path(json.loads(path.read_text())['profiles'][0]['runtime_directory'])/'mt5_health.json'
    assert health.exists() and json.loads(health.read_text())['connection_status']==item['connection_status']

def test_no_order_api_or_live_execution_flag_exposed():
    import afip.four_profile_operations.mt5_connection as module
    source=Path(module.__file__).read_text()
    assert 'order_send' not in source and 'live_execution: bool = False' in source and 'direct_execution: bool = False' in source
