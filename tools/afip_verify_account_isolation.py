from __future__ import annotations
import argparse, json, os
from pathlib import Path
from typing import Any
from afip.four_profile_operations.runtime import FourProfileOperationalRuntime

def value(obj: Any, name: str, default: Any=None) -> Any:
    if obj is None: return default
    if isinstance(obj, dict): return obj.get(name, default)
    return getattr(obj, name, default)

def normalize(path: str) -> str:
    try: return str(Path(path).resolve()).rstrip("\\/").casefold()
    except OSError: return str(path).rstrip("\\/").casefold()

def verify(config: Path) -> dict[str, Any]:
    profiles=FourProfileOperationalRuntime(config).load()
    rows=[]; errors=[]; seen_login={}; seen_folder={}
    for p in profiles:
        if not p.enabled:
            rows.append({'profile_id':p.profile_id,'status':'SKIPPED','reason':'profile_disabled'})
            continue
        if not p.login or not p.password_configured:
            errors.append(f'{p.profile_id}:credentials_missing'); rows.append({'profile_id':p.profile_id,'status':'BLOCKED','reason':'credentials_missing'}); continue
        folder=normalize(str(p.mt5_folder)); login=str(p.login)
        if folder in seen_folder: errors.append(f'duplicate_terminal:{seen_folder[folder]}:{p.profile_id}')
        seen_folder[folder]=p.profile_id
        if login in seen_login: errors.append(f'duplicate_login:{seen_login[login]}:{p.profile_id}')
        seen_login[login]=p.profile_id
        mt5=None
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
            ok=mt5.initialize(path=str(p.mt5_terminal),login=int(login),password=os.environ.get(p.password_env,''),server=p.server,timeout=60000,portable=True)
            if not ok:
                reason=f'initialize_failed:{mt5.last_error()}'; errors.append(f'{p.profile_id}:{reason}'); rows.append({'profile_id':p.profile_id,'status':'BLOCKED','reason':reason}); continue
            acc=mt5.account_info(); term=mt5.terminal_info()
            actual_login=str(value(acc,'login','')); actual_server=str(value(acc,'server','')); actual_path=str(value(term,'path','') or '')
            login_ok=actual_login==login; server_ok=actual_server.casefold()==p.server.casefold(); path_ok=normalize(actual_path)==folder
            ok_all=login_ok and server_ok and path_ok
            if not ok_all: errors.append(f'{p.profile_id}:binding_mismatch')
            rows.append({'profile_id':p.profile_id,'status':'PASS' if ok_all else 'BLOCKED','mode':'EXECUTION' if p.execution_enabled else 'RESEARCH_ONLY','configured_login':f'****{login[-4:]}','actual_login':f'****{actual_login[-4:]}' if actual_login else 'UNKNOWN','configured_server':p.server,'actual_server':actual_server or 'UNKNOWN','configured_terminal':str(p.mt5_folder),'actual_terminal':actual_path or 'UNKNOWN','login_match':login_ok,'server_match':server_ok,'terminal_match':path_ok})
        except Exception as exc:
            reason=f'{type(exc).__name__}:{exc}'; errors.append(f'{p.profile_id}:{reason}'); rows.append({'profile_id':p.profile_id,'status':'BLOCKED','reason':reason})
        finally:
            try:
                if mt5 is not None: mt5.shutdown()
            except Exception: pass
    return {'schema_version':'afip-account-isolation.v2','status':'PASS' if not errors else 'BLOCKED','safe_to_start':not errors,'execution_model':'SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5','errors':errors,'profiles':rows}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='config/four_profile_demo.json'); ap.add_argument('--output',default='runtime/account_isolation_status.json'); args=ap.parse_args()
    report=verify(Path(args.config)); out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2)); return 0 if report['safe_to_start'] else 2
if __name__=='__main__': raise SystemExit(main())
