"""A27 explicitly approved active read-only Demo/terminal/GOLD# identity proof."""
from __future__ import annotations
from datetime import datetime, timezone
import json,os
from pathlib import Path
import sys
from typing import Any,Iterable

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager

def _value(obj:Any,name:str,default:Any=None)->Any:
    return obj.get(name,default) if isinstance(obj,dict) else getattr(obj,name,default)

def capture(project_root:Path,approved:bool)->dict[str,Any]:
    if not approved:raise ValueError("active read-only proof requires --approve-active-readonly")
    root=project_root.resolve();manager=MT5MultiTerminalConnectionManager(root/"config/four_profile_demo.json")
    profiles=manager.operations.load();errors=manager.operations.validate(profiles)
    running=manager._running_terminal_paths()
    expected={manager._normal_path(p.mt5_terminal) for p in profiles if p.enabled}
    if errors or not expected or not expected.issubset(running):
        return {"schema":"afip.a27.active_readonly_demo_identity.v1","status":"BLOCKED",
          "reason":"passive_mapping_not_ready","validation_errors":list(errors),"orders_sent":False,
          "order_check_called":False,"order_send_called":False,"execution_authority":"NONE","profiles":[]}
    import MetaTrader5 as mt5
    demo_mode=getattr(mt5,"ACCOUNT_TRADE_MODE_DEMO",None);results=[]
    for profile in profiles:
        if not profile.enabled:continue
        initialized=False
        try:
            password=os.environ.get(profile.password_env,"")
            initialized=bool(mt5.initialize(path=str(profile.mt5_terminal),login=int(profile.login),
                password=password,server=profile.server,portable=True))
            account=mt5.account_info() if initialized else None
            terminal=mt5.terminal_info() if initialized else None
            symbol=mt5.symbol_info(profile.symbol) if initialized else None
            tick=mt5.symbol_info_tick(profile.symbol) if initialized and symbol is not None else None
            actual_login=str(_value(account,"login",""));trade_mode=_value(account,"trade_mode")
            is_demo=(demo_mode is not None and trade_mode is not None and int(trade_mode)==int(demo_mode))
            server=str(_value(account,"server",""));connected=bool(_value(terminal,"connected",False))
            results.append({"profile_id":profile.profile_id,"initialized":initialized,"connected":connected,
              "account_match":actual_login==str(profile.login),"server_match":server.casefold()==profile.server.casefold(),
              "demo_identity_verified":is_demo,"trade_mode":str(trade_mode),
              "account":f"****{actual_login[-4:]}" if actual_login else "UNAVAILABLE","server":server,
              "symbol":profile.symbol,"symbol_available":symbol is not None,"tick_available":tick is not None,
              "bid":_value(tick,"bid"),"ask":_value(tick,"ask"),"terminal_path":str(profile.mt5_terminal),
              "order_check_called":False,"order_send_called":False,"orders_sent":False})
        except Exception as exc:
            results.append({"profile_id":profile.profile_id,"initialized":initialized,"connected":False,
              "demo_identity_verified":False,"reason":f"{type(exc).__name__}:{exc}",
              "order_check_called":False,"order_send_called":False,"orders_sent":False})
        finally:
            try:mt5.shutdown()
            except Exception:pass
    ready=(len(results)==4 and all(item.get(key) is True for item in results for key in
        ("initialized","connected","account_match","server_match","demo_identity_verified","symbol_available","tick_available")))
    return {"schema":"afip.a27.active_readonly_demo_identity.v1",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "status":"ACTIVE_READONLY_DEMO_PROOF_PASS" if ready else "BLOCKED",
      "reason":"all_demo_profiles_and_gold_tick_verified" if ready else "active_readonly_identity_check_failed",
      "demo_identity_verified":ready,"orders_sent":False,"order_check_called":False,
      "order_send_called":False,"execution_authority":"NONE","automatic_trading_enabled_by_audit":False,
      "profiles":results,"next_required_proof":"separately_authorized_demo_order_lifecycle" if ready else "repair_identity_or_binding"}

def main(argv:Iterable[str]|None=None)->int:
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--project-root",required=True);p.add_argument("--output")
    p.add_argument("--approve-active-readonly",action="store_true");a=p.parse_args(argv)
    try:r=capture(Path(a.project_root),a.approve_active_readonly)
    except ValueError as exc:print(str(exc));return 2
    encoded=json.dumps(r,indent=2,ensure_ascii=False)
    if a.output:path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(encoded+"\n",encoding="utf-8")
    print(encoded);return 0
if __name__=="__main__":raise SystemExit(main())
