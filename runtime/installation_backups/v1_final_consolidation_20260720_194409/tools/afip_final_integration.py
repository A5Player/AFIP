from __future__ import annotations
import argparse,json,time
from pathlib import Path
from afip.final_integration import ArchitectureRegistry,FinalIntegrationRuntime,UnifiedDashboardAuthority,UnifiedResearchEngine

def main()->int:
 p=argparse.ArgumentParser();p.add_argument('command',choices=('start','stop','status','dashboard','research-once','research-forever','architecture'));p.add_argument('--root',default='.');p.add_argument('--interval',type=int,default=300);a=p.parse_args();root=Path(a.root).resolve();runtime=FinalIntegrationRuntime(root)
 if a.command=='start':value=runtime.start().as_dict()
 elif a.command=='stop':value=runtime.stop().as_dict()
 elif a.command=='status':value=runtime.status().as_dict()
 elif a.command=='dashboard':value={'dashboard':str(UnifiedDashboardAuthority(root).build())}
 elif a.command=='architecture':value=ArchitectureRegistry(root).inspect().as_dict()
 elif a.command=='research-once':value=UnifiedResearchEngine(root).run_once();UnifiedDashboardAuthority(root).build()
 else:
  engine=UnifiedResearchEngine(root);stop=root/'runtime/control/final_integration/stop_research_runtime.flag';cycles=0
  while not stop.exists():
   engine.run_once();UnifiedDashboardAuthority(root).build();cycles+=1
   for _ in range(max(1,a.interval//5)):
    if stop.exists():break
    time.sleep(min(5,a.interval))
  value={'status':'STOPPED','cycles':cycles}
 print(json.dumps(value,ensure_ascii=False,indent=2,default=str));return 0
if __name__=='__main__':raise SystemExit(main())
