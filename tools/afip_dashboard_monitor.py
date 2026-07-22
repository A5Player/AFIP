from __future__ import annotations
import argparse, json, os, signal, time
from pathlib import Path
from afip.final_integration.dashboard import UnifiedDashboardAuthority
from afip.final_integration.io import atomic_json, utc_now

_STOP=False

def _stop(*_):
    global _STOP; _STOP=True

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--root',default='.'); p.add_argument('--interval',type=float,default=2.0)
    a=p.parse_args(); root=Path(a.root).resolve(); interval=max(1.0,float(a.interval))
    for s in (signal.SIGINT,signal.SIGTERM):
        try: signal.signal(s,_stop)
        except Exception: pass
    status_path=root/'runtime/dashboard/dashboard_monitor_status.json'
    cycles=0
    while not _STOP:
        started=time.time()
        try:
            path=UnifiedDashboardAuthority(root).build(); cycles+=1
            atomic_json(status_path,{'status':'RUNNING','cycles':cycles,'dashboard':str(path),'updated_at_utc':utc_now(),'refresh_interval_seconds':interval,'execution_authority':False})
        except Exception as exc:
            atomic_json(status_path,{'status':'ERROR','cycles':cycles,'reason':f'{type(exc).__name__}:{exc}','updated_at_utc':utc_now(),'refresh_interval_seconds':interval,'execution_authority':False})
        elapsed=time.time()-started
        time.sleep(max(0.2,interval-elapsed))
    atomic_json(status_path,{'status':'STOPPED','cycles':cycles,'updated_at_utc':utc_now(),'refresh_interval_seconds':interval,'execution_authority':False})
    return 0
if __name__=='__main__': raise SystemExit(main())
