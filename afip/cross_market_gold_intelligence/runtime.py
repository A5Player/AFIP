"""Collect real MT5 cross-market bars and build research-only gold relationships."""
from __future__ import annotations
import json, math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable

DATA_UNAVAILABLE="DATA_UNAVAILABLE"
HORIZONS={"24H":24,"3D":72,"5D":120,"7D":168}

def _now(): return datetime.now(timezone.utc)
def _safe_float(v: Any) -> float | None:
    try:
        x=float(v); return x if math.isfinite(x) else None
    except (TypeError,ValueError): return None

def _corr(xs:list[float],ys:list[float])->float|None:
    n=min(len(xs),len(ys))
    if n<3:return None
    xs=xs[-n:];ys=ys[-n:];mx=fmean(xs);my=fmean(ys);dx=[x-mx for x in xs];dy=[y-my for y in ys]
    den=math.sqrt(sum(x*x for x in dx)*sum(y*y for y in dy))
    return sum(a*b for a,b in zip(dx,dy))/den if den else None

def _returns(closes:list[float])->list[float]: return [(b/a)-1.0 for a,b in zip(closes,closes[1:]) if a]

def _direction(value: float|None, neutral: float=0.001)->str:
    if value is None:return "UNKNOWN"
    return "BULLISH" if value>neutral else "BEARISH" if value < -neutral else "NEUTRAL"

@dataclass(frozen=True)
class SourceSpec:
    source_id:str; category:str; aliases:tuple[str,...]

class CrossMarketGoldResearchRuntime:
    """Read-only collector. It never sends orders and never certifies trading by assumption."""
    def __init__(self, project_root:str|Path=".", config_path:str|Path="config/cross_market_gold_intelligence.json"):
        self.root=Path(project_root); self.config_path=self.root/config_path
    def _config(self)->dict[str,Any]:
        return json.loads(self.config_path.read_text(encoding="utf-8"))
    def _specs(self,cfg:dict[str,Any])->list[SourceSpec]:
        return [SourceSpec(str(x["source_id"]),str(x["category"]),tuple(str(a) for a in x.get("aliases",()))) for x in cfg.get("sources",[]) if x.get("source_id")]
    @staticmethod
    def _resolve(mt5:Any,aliases:Iterable[str])->str|None:
        for alias in aliases:
            info=mt5.symbol_info(alias)
            if info is not None:
                if not getattr(info,"visible",False): mt5.symbol_select(alias,True)
                return alias
        return None
    @staticmethod
    def _closes(rows:Any)->list[float]:
        result=[]
        if rows is None:return result
        for row in rows:
            value=row[4] if not hasattr(row,"dtype") else row["close"]
            parsed=_safe_float(value)
            if parsed is not None:result.append(parsed)
        return result
    def collect(self)->dict[str,Any]:
        cfg=self._config(); now=_now(); rows=[]; gold_closes=[]; mt5=None; init_error=DATA_UNAVAILABLE
        try:
            import MetaTrader5 as mt5_module  # type: ignore
            mt5=mt5_module
            terminal=str(cfg.get("terminal_path","")).strip()
            initialized=mt5.initialize(path=terminal) if terminal else mt5.initialize()
            if not initialized: init_error=f"mt5_initialize_failed:{mt5.last_error()}"
        except Exception as exc: init_error=f"mt5_unavailable:{type(exc).__name__}:{exc}"
        if mt5 is not None and init_error==DATA_UNAVAILABLE:
            gold_symbol=self._resolve(mt5,tuple(cfg.get("gold_aliases",("GOLD#","XAUUSD"))))
            if gold_symbol:
                gold_closes=self._closes(mt5.copy_rates_from_pos(gold_symbol,mt5.TIMEFRAME_H1,1,int(cfg.get("maximum_bars",5000))))
            for spec in self._specs(cfg):
                symbol=self._resolve(mt5,spec.aliases); closes=self._closes(mt5.copy_rates_from_pos(symbol,mt5.TIMEFRAME_H1,1,int(cfg.get("maximum_bars",5000)))) if symbol else []
                research={}; ret=_returns(closes); gold_ret=_returns(gold_closes)
                for label,hours in HORIZONS.items():
                    available=min(len(closes),hours+1); change=(closes[-1]/closes[-available]-1.0) if available>=2 else None
                    sample=min(len(ret),len(gold_ret),hours); correlation=_corr(ret[-sample:],gold_ret[-sample:]) if sample>=3 else None
                    confidence=round(min(100.0,sample/max(hours,1)*100.0)*abs(correlation),2) if correlation is not None else DATA_UNAVAILABLE
                    research[label]={"direction":_direction(change),"magnitude_percent":round(change*100,4) if change is not None else DATA_UNAVAILABLE,"confidence_percent":confidence,"sample_size":sample,"correlation":round(correlation,6) if correlation is not None else DATA_UNAVAILABLE,"win_rate_percent":DATA_UNAVAILABLE,"market_regime":DATA_UNAVAILABLE,"session":"H1_MULTI_SESSION","volatility":DATA_UNAVAILABLE,"confirmation":DATA_UNAVAILABLE,"reversal":DATA_UNAVAILABLE,"indicator_role":"RESEARCH_REQUIRED"}
                rows.append({"source_id":spec.source_id,"category":spec.category,"status":"CONNECTED" if closes else "DATA_UNAVAILABLE","source":f"MT5:{symbol}" if symbol else DATA_UNAVAILABLE,"last_update":now.isoformat().replace("+00:00","Z") if closes else DATA_UNAVAILABLE,"data_age_seconds":0 if closes else DATA_UNAVAILABLE,"freshness":"FRESH" if closes else "UNKNOWN","research_samples":min(len(ret),len(gold_ret)),"horizons":research,"trading_eligible":False,"certification_status":"RESEARCH_ONLY","error_reason":DATA_UNAVAILABLE if closes else "symbol_or_rates_unavailable"})
            mt5.shutdown()
        connected=sum(r["status"]=="CONNECTED" for r in rows)
        gold_24h_change=((gold_closes[-1]/gold_closes[-25])-1.0)*100.0 if len(gold_closes)>=25 else None
        return {"schema_version":"phase_u_pack_3_4_10","generated_at":now.isoformat().replace("+00:00","Z"),"gold_24h_change_percent":round(gold_24h_change,6) if gold_24h_change is not None else DATA_UNAVAILABLE,"pipeline":["RAW_DATA","NORMALIZED_DATA","FEATURE_ENGINEERING","RESEARCH_DATABASE","KNOWLEDGE_DATABASE","CERTIFICATION","TRADING_INTELLIGENCE"],"pipeline_stage":"RESEARCH_DATABASE","execution_authority":False,"gold_samples":max(0,len(gold_closes)-1),"sources":rows,"connected_sources":connected,"configured_sources":len(self._specs(cfg)),"connection_error":init_error,"overall_cross_market_health_percent":round(connected/max(1,len(self._specs(cfg)))*100,2)}
    def write(self,output:str|Path="runtime/research/cross_market/latest.json")->Path:
        report=self.collect(); path=self.root/output; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        ledger=path.parent/"observations.jsonl"
        with ledger.open("a",encoding="utf-8") as handle: handle.write(json.dumps(report,ensure_ascii=False,separators=(",",":"))+"\n")
        return path
