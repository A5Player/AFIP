from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from afip.research_live_dashboard import build_live_snapshot, write_live_dashboard
p=argparse.ArgumentParser();p.add_argument('--root',default='.')
a=p.parse_args();snapshot=build_live_snapshot(a.root);path=write_live_dashboard(a.root,snapshot)
print(json.dumps({'status':'PASS','dashboard':str(path),'execution_authority':False},indent=2))
