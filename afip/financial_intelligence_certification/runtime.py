"""Real-source-only certification for financial and intelligence runtime data."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
VERIFIED_SOURCE_STATES = {"CONNECTED", "VERIFIED", "AVAILABLE"}

def _utcnow() -> datetime: return datetime.now(timezone.utc)
def _parse_time(value: Any) -> datetime | None:
    if value in (None, "", DATA_UNAVAILABLE): return None
    try:
        text=str(value).strip().replace("Z", "+00:00")
        result=datetime.fromisoformat(text)
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)
    except (TypeError, ValueError): return None

def _number(value: Any) -> float | str:
    if value in (None, "", DATA_UNAVAILABLE): return DATA_UNAVAILABLE
    try: return round(float(value), 2)
    except (TypeError, ValueError): return DATA_UNAVAILABLE

def _load(path: Path) -> dict[str, Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError, UnicodeError): return {}

def _age(updated_at: Any, now: datetime) -> float | str:
    stamp=_parse_time(updated_at)
    return round(max(0.0, (now-stamp).total_seconds()), 3) if stamp else DATA_UNAVAILABLE

def _fresh(age: float | str, threshold: int) -> str:
    if not isinstance(age, (int, float)): return "UNKNOWN"
    return "FRESH" if age <= threshold else "STALE"

class FinancialIntegrityRuntime:
    """Read P1-P4 snapshots without manufacturing missing monetary values."""
    def __init__(self, project_root: str | Path=".", freshness_seconds: int=120):
        self.root=Path(project_root); self.freshness_seconds=int(freshness_seconds)

    def _profile(self, profile_id: str, now: datetime) -> dict[str, Any]:
        base=self.root/"runtime"/"profiles"/profile_id.lower()
        candidates=(base/"financial_status.json", base/"status.json", base/"mt5_health.json")
        merged: dict[str, Any]={}; used=[]
        for path in candidates:
            if path.exists():
                data=_load(path)
                if data: merged.update(data); used.append(str(path.relative_to(self.root)))
        source_state=str(merged.get("financial_connection_status", merged.get("connection_status", merged.get("mt5_connection", "UNKNOWN")))).upper()
        source=str(merged.get("financial_data_source", merged.get("account_data_source", DATA_UNAVAILABLE)))
        updated=merged.get("financial_last_update", merged.get("last_update", merged.get("updated_at", merged.get("checked_at"))))
        age=_age(updated, now); verified=source_state in VERIFIED_SOURCE_STATES and source != DATA_UNAVAILABLE and bool(used)
        def money(*keys: str) -> float | str:
            if not verified: return DATA_UNAVAILABLE
            for key in keys:
                if key in merged: return _number(merged.get(key))
            return DATA_UNAVAILABLE
        balance=money("account_balance", "balance")
        equity=money("account_equity", "equity")
        allocation=money("available_allocation", "allocation")
        return {
            "profile_id":profile_id.upper(), "status":"VERIFIED" if verified else "DATA_UNAVAILABLE",
            "data_source":source if verified else DATA_UNAVAILABLE, "source_files":used,
            "last_update":updated if _parse_time(updated) else DATA_UNAVAILABLE,
            "data_age_seconds":age, "data_freshness":_fresh(age,self.freshness_seconds),
            "retry_status":merged.get("financial_retry_status", merged.get("retry_status", DATA_UNAVAILABLE)),
            "retry_count":merged.get("financial_retry_count", merged.get("retry_count", 0 if verified else DATA_UNAVAILABLE)),
            "connection_status":source_state if source_state else "UNKNOWN",
            "error_reason":merged.get("financial_error_reason", merged.get("error_reason", DATA_UNAVAILABLE)),
            "currency":merged.get("account_currency", merged.get("currency", DATA_UNAVAILABLE)) if verified else DATA_UNAVAILABLE,
            "balance":balance, "equity":equity, "available_allocation":allocation,
            "margin":money("account_margin", "margin"), "free_margin":money("account_margin_free", "free_margin"),
        }

    def evaluate(self) -> dict[str, Any]:
        now=_utcnow(); profiles=[self._profile(f"P{i}",now) for i in range(1,5)]
        numeric=lambda key:[p[key] for p in profiles if isinstance(p.get(key),(int,float))]
        totals={key:(round(sum(numeric(key)),2) if len(numeric(key))==4 else DATA_UNAVAILABLE) for key in ("balance","equity","available_allocation","margin","free_margin")}
        return {"schema_version":"phase_u_pack_3_4_9","generated_at":now.isoformat().replace("+00:00","Z"),"policy":"REAL_SOURCE_ONLY","profiles":profiles,"portfolio_total":{"status":"VERIFIED" if all(p["status"]=="VERIFIED" for p in profiles) else "DATA_UNAVAILABLE",**totals}}

    def write(self, output: str | Path="runtime/certification/financial_integrity.json") -> Path:
        path=self.root/output; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(self.evaluate(),ensure_ascii=False,indent=2),encoding="utf-8"); return path

class IntelligenceSourceCertificationRuntime:
    SOURCES=("news","economic_calendar","cot","gold_etf","bond_yield","real_yield","dollar_index","market_regime","research_runtime")
    def __init__(self, project_root: str | Path=".", freshness_seconds: int=3600): self.root=Path(project_root); self.freshness_seconds=int(freshness_seconds)
    def evaluate(self) -> dict[str, Any]:
        now=_utcnow(); rows=[]
        for name in self.SOURCES:
            path=self.root/"runtime"/"intelligence"/"source_snapshots"/f"{name}.json"; data=_load(path) if path.exists() else {}
            source=str(data.get("source",DATA_UNAVAILABLE)); state=str(data.get("connection_status",data.get("status","UNKNOWN"))).upper(); updated=data.get("last_update",data.get("updated_at")); age=_age(updated,now)
            verified=bool(data) and source != DATA_UNAVAILABLE and state in VERIFIED_SOURCE_STATES and _parse_time(updated) is not None
            rows.append({"source_id":name,"status":"VERIFIED" if verified else "DATA_UNAVAILABLE","source":source if verified else DATA_UNAVAILABLE,"last_update":updated if verified else DATA_UNAVAILABLE,"refresh_interval_seconds":data.get("refresh_interval_seconds",DATA_UNAVAILABLE),"data_age_seconds":age,"freshness":_fresh(age,self.freshness_seconds),"error_reason":data.get("error_reason",DATA_UNAVAILABLE),"retry_count":data.get("retry_count",0 if verified else DATA_UNAVAILABLE),"connection_status":state,"snapshot_path":str(path.relative_to(self.root)) if path.exists() else DATA_UNAVAILABLE})
        verified=sum(r["status"]=="VERIFIED" for r in rows)
        return {"schema_version":"phase_u_pack_3_4_9","generated_at":now.isoformat().replace("+00:00","Z"),"sources":rows,"verified_sources":verified,"source_count":len(rows),"overall_intelligence_health_percent":round(verified/len(rows)*100,2)}
    def write(self, output: str | Path="runtime/certification/intelligence_sources.json") -> Path:
        path=self.root/output; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(self.evaluate(),ensure_ascii=False,indent=2),encoding="utf-8"); return path
