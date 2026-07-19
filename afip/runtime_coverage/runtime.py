"""Deterministic runtime coverage matrix for Phase U Pack 1."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class CoverageItem:
    component_id: str
    title: str
    code_available: bool
    runtime_connected: bool
    dataset_registered: bool
    decision_trace_available: bool
    dashboard_visible: bool
    test_covered: bool
    status: str
    next_action: str
    def as_dict(self)->dict[str,Any]: return asdict(self)

@dataclass(frozen=True)
class RuntimeCoverageReport:
    status: str
    total_components: int
    connected_components: int
    dashboard_visible_components: int
    complete_components: int
    coverage_percent: float
    execution_permission: bool
    items: tuple[CoverageItem,...]
    def as_dict(self)->dict[str,Any]:
        d=asdict(self); d["items"]=[x.as_dict() for x in self.items]; return d

class RuntimeCoverageRuntime:
    COMPONENTS=(
      ("market_intelligence","Market Intelligence"),("market_regime","Market Regime"),
      ("decision_intelligence","Decision Intelligence"),("complete_trade_plan","Complete Trade Plan"),
      ("trade_plan_runtime","Trade Plan Runtime"),("capital_allocation","Capital Allocation"),
      ("position_policy","Position Policy"),("trading_cost","Trading Cost Approval"),
      ("execution_gate","Execution Gate"),("position_care","Position Care"),
      ("unattended_continuity","Unattended Continuity"),("research_data","Research Data Foundation"),
      ("financial_data_lake","Financial Data Lake"),("dashboard_runtime","Dashboard Runtime"),
    )
    DEFAULT_CONNECTED={"market_intelligence","market_regime","decision_intelligence","capital_allocation","position_policy","trading_cost","execution_gate","dashboard_runtime"}
    DEFAULT_DATASETS={"complete_trade_plan","trade_plan_runtime","position_care","unattended_continuity","research_data","financial_data_lake"}
    DEFAULT_TRACES={"decision_intelligence","complete_trade_plan","trade_plan_runtime","capital_allocation","position_policy","trading_cost","execution_gate","position_care","unattended_continuity"}
    def evaluate_one(self, record: Mapping[str,Any])->RuntimeCoverageReport:
        connected=set(record.get("runtime_connected_components", self.DEFAULT_CONNECTED))
        datasets=set(record.get("dataset_registered_components", self.DEFAULT_DATASETS))
        traces=set(record.get("decision_trace_components", self.DEFAULT_TRACES))
        visible=set(record.get("dashboard_visible_components", connected|{"complete_trade_plan","trade_plan_runtime","position_care","unattended_continuity","research_data","financial_data_lake"}))
        tested=set(record.get("test_covered_components", {x[0] for x in self.COMPONENTS}))
        unavailable=set(record.get("code_unavailable_components", ()))
        items=[]
        for cid,title in self.COMPONENTS:
            code=cid not in unavailable; runtime=cid in connected; data=cid in datasets; trace=cid in traces; dash=cid in visible; test=cid in tested
            complete=code and runtime and dash and test and (data or cid in {"market_intelligence","market_regime","trading_cost","execution_gate","dashboard_runtime"})
            status="COMPLETE" if complete else ("CONNECTED" if runtime else ("FOUNDATION_ONLY" if code else "UNAVAILABLE"))
            next_action="none" if complete else ("wire_into_primary_runtime" if code and not runtime else "complete_observability_evidence")
            items.append(CoverageItem(cid,title,code,runtime,data,trace,dash,test,status,next_action))
        connected_count=sum(x.runtime_connected for x in items); dash_count=sum(x.dashboard_visible for x in items); complete_count=sum(x.status=="COMPLETE" for x in items)
        pct=round((complete_count/len(items))*100,2)
        return RuntimeCoverageReport("READY" if complete_count==len(items) else "INTEGRATION_REQUIRED",len(items),connected_count,dash_count,complete_count,pct,False,tuple(items))
