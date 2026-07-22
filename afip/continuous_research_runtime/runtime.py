from __future__ import annotations
import json, math, time
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any
from afip.cross_market_gold_intelligence import CrossMarketGoldResearchRuntime
from afip.automatic_research_runtime import AutomaticResearchRuntime

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
        self.root=Path(root); self.ledger=self.root/'runtime/research/cross_market/observations.jsonl'
    def build(self)->dict[str,Any]:
        observations=[]
        if self.ledger.exists():
            for line in self.ledger.read_text(encoding='utf-8').splitlines():
                try: observations.append(json.loads(line))
                except json.JSONDecodeError: continue
        by_source={}
        for obs in observations:
            for src in obs.get('sources',[]):
                sid=src.get('source_id'); h=src.get('horizons',{}).get('24H',{}); mag=_num(h.get('magnitude_percent'))
                if sid and mag is not None: by_source.setdefault(sid,[]).append(mag)
        relationships=[]; gold_series=[_num(o.get('gold_24h_change_percent')) for o in observations]
        for sid,values in sorted(by_source.items()):
            usable_gold=[x for x in gold_series if x is not None]; corr=_pearson(values,usable_gold) if usable_gold else None; n=len(values)
            relationships.append({'source_id':sid,'sample_size':n,'tested_period_start':observations[0].get('generated_at') if observations else DATA_UNAVAILABLE,
                'tested_period_end':observations[-1].get('generated_at') if observations else DATA_UNAVAILABLE,'correlation':round(corr,6) if corr is not None else DATA_UNAVAILABLE,
                'influence_score_percent':round(abs(corr)*100,2) if corr is not None else DATA_UNAVAILABLE,'stability_score_percent':round(min(100.0,n/1000*100),2),
                'statistical_confidence':DATA_UNAVAILABLE if n<30 else 'PRELIMINARY','certification_status':'RESEARCH_ONLY','trading_eligible':False,
                'last_certified':DATA_UNAVAILABLE,'evidence_requirements':{'minimum_samples':1000,'minimum_regime_coverage':4,'human_review_required':True}})
        return {'schema_version':'phase_u_pack_3_4_11','generated_at':_utc(),'execution_authority':False,'observation_count':len(observations),'relationships':relationships}
    def write(self):
        out=self.root/'runtime/research/cross_market/evidence.json';out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(self.build(),ensure_ascii=False,indent=2),encoding='utf-8');return out

class ContinuousResearchRuntime:
    """Unified research cycle: MT5 M1-D1 -> lake -> replay -> cross-market -> dashboard evidence."""
    def __init__(self, root: str|Path='.', interval_seconds:int=300, maximum_replay_bars:int=5000):
        self.root=Path(root); self.interval=max(60,int(interval_seconds)); self.maximum_replay_bars=max(500,int(maximum_replay_bars))
        self.stop_file=self.root/'runtime/control/stop_cross_market_research.flag'; self.status_path=self.root/'runtime/research/continuous_research_status.json'
    def _status(self, status:str, stage:str, reason:str, **extra:Any)->dict[str,Any]:
        payload={'schema_version':'phase_u_pack_3_4_11','status':status,'stage':stage,'reason':reason,'updated_at_utc':_utc(),
                 'interval_seconds':self.interval,'execution_authority':False,'live_execution_enabled':False,'order_send_called':False,**extra}
        self.status_path.parent.mkdir(parents=True,exist_ok=True); self.status_path.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8'); return payload
    def run_once(self):
        started=_utc(); self._status('RUNNING','MT5_TIMEFRAME_COLLECTION','loading_closed_bars_M1_to_D1',cycle_started_at_utc=started)
        auto=AutomaticResearchRuntime(self.root, progress=print).run(collect_mt5_when_needed=True, maximum_replay_bars=self.maximum_replay_bars)
        self._status('RUNNING','CROSS_MARKET_RESEARCH','automatic_history_and_replay_complete',cycle_started_at_utc=started,automatic_research=auto.as_dict())
        latest=CrossMarketGoldResearchRuntime(self.root).write(); evidence=EvidenceResearchEngine(self.root).write()
        result=self._status('COMPLETE','WAITING_NEXT_CYCLE','cycle_complete_waiting_for_next_interval',cycle_started_at_utc=started,last_cycle=_utc(),
            automatic_research=auto.as_dict(),latest=str(latest),evidence=str(evidence),next_cycle_not_before_utc='INTERVAL_SECONDS_AFTER_COMPLETION')
        try:
            from afip.dashboard_ui.research_operations import write_research_operations_dashboard
            write_research_operations_dashboard(self.root/'runtime/dashboard', self.root)
        except Exception as exc:
            result['dashboard_warning']=f'{type(exc).__name__}: {exc}'
        return result
    def run_forever(self, max_cycles:int|None=None):
        self.stop_file.parent.mkdir(parents=True,exist_ok=True);cycles=0
        while not self.stop_file.exists():
            self.run_once();cycles+=1
            if max_cycles is not None and cycles>=max_cycles:break
            remaining=self.interval
            while remaining>0 and not self.stop_file.exists():
                time.sleep(min(5,remaining));remaining-=min(5,remaining)
        return cycles
