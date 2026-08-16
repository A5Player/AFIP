"""A31 profile-neutral daily participation and setup-budget research."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime
import math
from typing import Any, Iterable, Mapping, Sequence

@dataclass(frozen=True)
class DailySetupOutcome:
    setup_id: str; decision_at_utc: str; partition: str; decision_score_percent: float; result_r: float
    initial_risk_r: float = 1.0; session_name: str = "UNCLASSIFIED"; pattern_family: str = "UNCLASSIFIED"
    broker_order_count: int = 1; unit_count: int = 1; future_data_used_for_decision: bool = False
    def __post_init__(self) -> None:
        if not self.setup_id.strip(): raise ValueError("setup_id is required")
        stamp=datetime.fromisoformat(self.decision_at_utc.replace("Z","+00:00"))
        if stamp.tzinfo is None: raise ValueError("decision timestamp requires timezone")
        if self.partition not in {"TRAIN","VALIDATION","BLIND_FORWARD"}: raise ValueError("invalid partition")
        if not 0 <= self.decision_score_percent <= 100: raise ValueError("decision score must be 0..100 percent")
        if not math.isfinite(self.result_r): raise ValueError("result_r must be finite")
        if self.initial_risk_r <= 0 or self.broker_order_count <= 0 or self.unit_count <= 0: raise ValueError("risk, order and unit counts must be positive")
        if self.future_data_used_for_decision: raise ValueError("future data is forbidden at decision time")
    @property
    def trading_day(self) -> str: return datetime.fromisoformat(self.decision_at_utc.replace("Z","+00:00")).date().isoformat()

@dataclass(frozen=True)
class DailyParticipationPolicy:
    policy_id: str; maximum_setups_per_day: int|None
    minimum_decision_score_percent: float=0.0; maximum_initial_risk_r_per_day: float|None=None
    one_per_session: bool=False; one_per_pattern_family: bool=False
    dynamic_score_bands: tuple[tuple[float,int],...]=()
    def __post_init__(self) -> None:
        if not self.policy_id.strip(): raise ValueError("policy_id is required")
        if self.maximum_setups_per_day is not None and self.maximum_setups_per_day < 0: raise ValueError("maximum setups cannot be negative")
        if not 0 <= self.minimum_decision_score_percent <= 100: raise ValueError("score threshold must be percent")
        if self.maximum_initial_risk_r_per_day is not None and self.maximum_initial_risk_r_per_day <= 0: raise ValueError("daily risk R must be positive")
    def daily_limit(self,best_score:float)->int|None:
        if not self.dynamic_score_bands: return self.maximum_setups_per_day
        limit=0
        for threshold,candidate_limit in sorted(self.dynamic_score_bands):
            if best_score>=threshold: limit=candidate_limit
        return limit

@dataclass(frozen=True)
class DailyParticipationResult:
    policy_id:str; partition:str; calendar_days:int; trading_days:int; no_trade_days:int; selected_setups:int
    broker_orders:int; units:int; wins:int; losses:int; win_rate_percent:float|None
    expectancy_r_per_setup:float|None; net_result_r:float; profit_factor_ratio:float|None; maximum_drawdown_r:float
    average_setups_per_calendar_day:float; average_setups_per_trading_day:float|None
    marginal_expectancy_r_by_daily_rank:Mapping[str,float]; execution_authority:str="NONE"; automatic_profile_assignment:bool=False
    def as_dict(self)->dict[str,Any]: return asdict(self)

DEFAULT_POLICIES=(
 DailyParticipationPolicy("SKIP_OR_TOP_1",1), DailyParticipationPolicy("TOP_0_TO_3",3),
 DailyParticipationPolicy("TOP_0_TO_5",5), DailyParticipationPolicy("TOP_0_TO_10",10),
 DailyParticipationPolicy("ONE_PER_SESSION",None,one_per_session=True),
 DailyParticipationPolicy("ONE_PER_PATTERN_FAMILY",None,one_per_pattern_family=True),
 DailyParticipationPolicy("DYNAMIC_DAILY_BUDGET",10,dynamic_score_bands=((70,1),(80,3),(90,5),(97,10))),
 DailyParticipationPolicy("SAFETY_BOUNDED_UNCAPPED",None,maximum_initial_risk_r_per_day=10.0),
)

class A31DailyParticipationResearch:
    @staticmethod
    def _select_day(rows:Sequence[DailySetupOutcome],policy:DailyParticipationPolicy)->list[DailySetupOutcome]:
        ordered=sorted(rows,key=lambda x:(-x.decision_score_percent,x.decision_at_utc,x.setup_id))
        if not ordered:return []
        limit=policy.daily_limit(ordered[0].decision_score_percent); selected=[]; sessions=set(); patterns=set(); risk=0.0
        for row in ordered:
            if row.decision_score_percent<policy.minimum_decision_score_percent:continue
            if limit is not None and len(selected)>=limit:break
            if policy.one_per_session and row.session_name in sessions:continue
            if policy.one_per_pattern_family and row.pattern_family in patterns:continue
            if policy.maximum_initial_risk_r_per_day is not None and risk+row.initial_risk_r>policy.maximum_initial_risk_r_per_day:continue
            selected.append(row);sessions.add(row.session_name);patterns.add(row.pattern_family);risk+=row.initial_risk_r
        return sorted(selected,key=lambda x:(x.decision_at_utc,x.setup_id))
    def evaluate(self,observations:Iterable[DailySetupOutcome],policies:Iterable[DailyParticipationPolicy]=DEFAULT_POLICIES)->tuple[DailyParticipationResult,...]:
        values=tuple(observations);policy_values=tuple(policies)
        if len({x.setup_id for x in values})!=len(values):raise ValueError("setup_id must be unique")
        if len({x.policy_id for x in policy_values})!=len(policy_values):raise ValueError("policy_id must be unique")
        results=[]
        for partition in ("TRAIN","VALIDATION","BLIND_FORWARD"):
            source=[x for x in values if x.partition==partition];by_day={}
            for item in source:by_day.setdefault(item.trading_day,[]).append(item)
            for policy in policy_values:
                selected=[];ranks={}
                for day in sorted(by_day):
                    chosen=self._select_day(by_day[day],policy);selected.extend(chosen)
                    for rank,item in enumerate(chosen,1):ranks.setdefault(rank,[]).append(item.result_r)
                pnl=[x.result_r for x in selected];wins=sum(x>0 for x in pnl);losses=sum(x<0 for x in pnl)
                gross_win=sum(x for x in pnl if x>0);gross_loss=-sum(x for x in pnl if x<0);equity=peak=drawdown=0.0
                for value in pnl:equity+=value;peak=max(peak,equity);drawdown=max(drawdown,peak-equity)
                trading_days=len({x.trading_day for x in selected});days=len(by_day)
                results.append(DailyParticipationResult(policy.policy_id,partition,days,trading_days,days-trading_days,len(selected),sum(x.broker_order_count for x in selected),sum(x.unit_count for x in selected),wins,losses,round(wins/len(selected)*100,6) if selected else None,round(sum(pnl)/len(selected),8) if selected else None,round(sum(pnl),8),round(gross_win/gross_loss,8) if gross_loss else None,round(drawdown,8),round(len(selected)/days,8) if days else 0.0,round(len(selected)/trading_days,8) if trading_days else None,{str(rank):round(sum(items)/len(items),8) for rank,items in sorted(ranks.items())}))
        return tuple(results)
    @staticmethod
    def rank_blind_forward(results:Iterable[DailyParticipationResult])->tuple[dict[str,Any],...]:
        rows=[x for x in results if x.partition=="BLIND_FORWARD" and x.selected_setups>0]
        rows.sort(key=lambda x:(-(x.expectancy_r_per_setup or -1e99),x.maximum_drawdown_r,-(x.profit_factor_ratio or 0),-x.net_result_r,x.policy_id))
        return tuple({"research_rank":rank,**item.as_dict(),"profile_strategy_selection":"NOT_DECIDED","automatic_research_promotion":False} for rank,item in enumerate(rows,1))
