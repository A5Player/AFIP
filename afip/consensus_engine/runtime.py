from __future__ import annotations
from datetime import datetime,timedelta,timezone
from typing import Any,Mapping
from .models import ConsensusContribution,ConsensusReport
class ConsensusEngineRuntime:
    DEFAULT_WEIGHTS={"market_regime":1.0,"market_structure":0.9,"multi_timeframe":0.85,"liquidity":0.7,"gold_macro":0.75,"central_bank":0.75,"cot":0.65,"open_interest":0.6,"etf_flow":0.65,"usd_index":0.75,"bond_yield":0.75}
    def evaluate_one(self,record:Mapping[str,Any])->ConsensusReport:
        now=record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now,datetime): now=datetime.fromisoformat(str(now).replace("Z","+00:00"))
        scores={"BUY":0.0,"SELL":0.0,"WAIT":0.0}; raw=[]
        for source,default_weight in self.DEFAULT_WEIGHTS.items():
            status=str(record.get(f"{source}_status","WAITING")).upper()
            if status!="READY": continue
            direction=str(record.get(f"{source}_direction",record.get(f"{source}_bias","WAIT"))).upper()
            direction={"BULLISH":"BUY","BEARISH":"SELL","NEUTRAL":"WAIT"}.get(direction,direction)
            if direction not in scores: direction="WAIT"
            try: confidence=max(0.0,min(1.0,float(record.get(f"{source}_confidence",0.0))))
            except: confidence=0.0
            try: weight=max(0.0,min(2.0,float(record.get(f"{source}_weight",default_weight))))
            except: weight=default_weight
            value=confidence*weight; scores[direction]+=value; raw.append((source,direction,confidence,weight,value))
        directional=scores["BUY"]+scores["SELL"]
        consensus="BUY" if scores["BUY"]>scores["SELL"] and scores["BUY"]>scores["WAIT"] else "SELL" if scores["SELL"]>scores["BUY"] and scores["SELL"]>scores["WAIT"] else "WAIT"
        total=sum(scores.values()) or 1.0
        agreement=scores[consensus]/total
        conflict=(min(scores["BUY"],scores["SELL"])/directional) if directional else 0.0
        quality="STRONG" if agreement>=0.70 and conflict<0.20 else "MODERATE" if agreement>=0.50 and conflict<0.35 else "WEAK"
        contrib=tuple(ConsensusContribution(s,d,round(c,4),round(w,4),round(v,4),d==consensus) for s,d,c,w,v in raw)
        dominant=tuple(c.source for c in sorted(contrib,key=lambda x:x.weighted_score,reverse=True) if c.agrees)[:3]
        contradict=tuple(c.source for c in sorted(contrib,key=lambda x:x.weighted_score,reverse=True) if c.direction not in {consensus,"WAIT"})[:3]
        status="READY" if len(contrib)>=3 and quality!="WEAK" else "WAITING"
        en=f"Use {consensus} consensus as decision context; validate risk and entry conditions next." if status=="READY" else "Wait for stronger agreement or additional reliable evidence."
        th=f"ใช้ฉันทามติ {consensus} เป็นบริบทการตัดสินใจ แล้วตรวจสอบความเสี่ยงและเงื่อนไขเข้าออเดอร์" if status=="READY" else "รอฉันทามติที่แข็งแรงขึ้นหรือหลักฐานที่เชื่อถือได้เพิ่มเติม"
        return ConsensusReport(status,consensus,quality,round(agreement,4),round(conflict,4),round(scores["BUY"],4),round(scores["SELL"],4),round(scores["WAIT"],4),dominant,contradict,en,th,(now.astimezone(timezone.utc)+timedelta(minutes=15)).isoformat(),contrib,False)
