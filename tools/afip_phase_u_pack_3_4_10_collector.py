from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from afip.continuous_research_runtime import ContinuousResearchRuntime
p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--interval-seconds',type=int,default=300);p.add_argument('--maximum-replay-bars',type=int,default=5000);p.add_argument('--once',action='store_true');p.add_argument('--max-cycles',type=int)
a=p.parse_args();rt=ContinuousResearchRuntime(Path(a.root).resolve(),a.interval_seconds,a.maximum_replay_bars)
result=rt.run_once() if a.once else {'cycles':rt.run_forever(a.max_cycles),'execution_authority':False}
print(json.dumps(result,indent=2,ensure_ascii=False))
