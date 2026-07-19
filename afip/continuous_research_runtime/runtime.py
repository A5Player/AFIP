from __future__ import annotations
import json, math, time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any
from afip.cross_market_gold_intelligence import CrossMarketGoldResearchRuntime

DATA_UNAVAILABLE='DATA_UNAVAILABLE'

def _utc(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def _num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except (TypeError,ValueError): return None

def _pearson(xs,ys):
    n=min(len(xs),len(ys))
    if n<10:return None
    xs=xs[-n:];ys=ys[-n:];mx=fmean(xs);my=fmean(ys)
    dx=[x-mx for x in xs];dy=[y-my for y in ys];den=math.sqrt(sum(x*x for x in dx)*sum(y*y for y in dy))
    return sum(a*b for a,b in zip(dx,dy))/den if den else None

class EvidenceResearchEngine:
    def __init__(self, root: str|Path='.'):
        self.root=Path(root)
        self.ledger=self.root/'runtime/research/cross_market/observations.jsonl'
    def build(self)->dict[str,Any]:
        observations=[]
        if self.ledger.exists():
            for line in self.ledger.read_text(encoding='utf-8').splitlines():
                try: observations.append(json.loads(line))
                except json.JSONDecodeError: continue
        by_source={}
        for obs in observations:
            for src in obs.get('sources',[]):
                sid=src.get('source_id'); h=src.get('horizons',{}).get('24H',{})
                mag=_num(h.get('magnitude_percent'))
                if sid and mag is not None: by_source.setdefault(sid,[]).append(mag)
        relationships=[]
        gold_series=[]
        for obs in observations:
            gold_series.append(_num(obs.get('gold_24h_change_percent')))
        for sid,values in sorted(by_source.items()):
            usable_gold=[x for x in gold_series if x is not None]
            corr=_pearson(values,usable_gold) if usable_gold else None
            n=len(values); stability=min(100.0,n/1000*100)
            relationships.append({
                'source_id':sid,'sample_size':n,'tested_period_start':observations[0].get('generated_at') if observations else DATA_UNAVAILABLE,
                'tested_period_end':observations[-1].get('generated_at') if observations else DATA_UNAVAILABLE,
                'correlation':round(corr,6) if corr is not None else DATA_UNAVAILABLE,
                'influence_score_percent':round(abs(corr)*100,2) if corr is not None else DATA_UNAVAILABLE,
                'stability_score_percent':round(stability,2),'statistical_confidence':DATA_UNAVAILABLE if n<30 else 'PRELIMINARY',
                'certification_status':'RESEARCH_ONLY','trading_eligible':False,'last_certified':DATA_UNAVAILABLE,
                'evidence_requirements':{'minimum_samples':1000,'minimum_regime_coverage':4,'human_review_required':True}
            })
        return {'schema_version':'phase_u_pack_3_4_10','generated_at':_utc(),'execution_authority':False,'observation_count':len(observations),'relationships':relationships}
    def write(self):
        out=self.root/'runtime/research/cross_market/evidence.json';out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(self.build(),ensure_ascii=False,indent=2),encoding='utf-8');return out

class ContinuousResearchRuntime:
    def __init__(self, root: str|Path='.', interval_seconds:int=300):
        self.root=Path(root);self.interval=max(60,int(interval_seconds));self.stop_file=self.root/'runtime/control/stop_cross_market_research.flag'
    def run_once(self):
        latest=CrossMarketGoldResearchRuntime(self.root).write()
        evidence=EvidenceResearchEngine(self.root).write()
        status={'schema_version':'phase_u_pack_3_4_10','last_cycle':_utc(),'status':'COMPLETE','latest':str(latest),'evidence':str(evidence),'interval_seconds':self.interval,'execution_authority':False}
        path=self.root/'runtime/research/cross_market/collector_status.json';path.write_text(json.dumps(status,indent=2),encoding='utf-8');return status
    def run_forever(self, max_cycles:int|None=None):
        self.stop_file.parent.mkdir(parents=True,exist_ok=True);cycles=0
        while not self.stop_file.exists():
            self.run_once();cycles+=1
            if max_cycles is not None and cycles>=max_cycles:break
            time.sleep(self.interval)
        return cycles
