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


class FinancialAnalyticsCertificationRuntime:
    """Read-only, cost-aware financial analytics over verified account snapshots and eligible closed trades."""

    PERIODS = ("daily", "weekly", "monthly", "yearly")

    def __init__(self, project_root: str | Path = ".", research_root: str | Path = "runtime/research"):
        self.root = Path(project_root)
        self.research_root = self.root / research_root

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            if value in (None, "", DATA_UNAVAILABLE):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _case_dimension(case: Mapping[str, Any], dimension: str) -> str:
        market = case.get("market_context", {}) if isinstance(case.get("market_context"), Mapping) else {}
        plan = case.get("plan_context", {}) if isinstance(case.get("plan_context"), Mapping) else {}
        entry = case.get("entry_context", {}) if isinstance(case.get("entry_context"), Mapping) else {}
        if dimension == "profile":
            return str(case.get("profile_id") or entry.get("profile_id") or "UNKNOWN")
        if dimension == "pattern":
            return str(market.get("pattern_id") or market.get("pattern") or "UNKNOWN")
        if dimension == "plan":
            return str(plan.get("plan_id") or case.get("plan_id") or "UNKNOWN")
        return "UNKNOWN"

    def _eligible_closed_cases(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in sorted((self.research_root / "trade_cases").glob("*.json")):
            case = _load(path)
            exit_context = case.get("exit_context", {}) if isinstance(case.get("exit_context"), Mapping) else {}
            if exit_context.get("research_feedback_status") != "ELIGIBLE":
                continue
            net = self._safe_float(exit_context.get("net_realized_profit_usd"))
            if net is None:
                continue
            rows.append(case)
        return rows

    @classmethod
    def _metrics(cls, cases: list[Mapping[str, Any]]) -> dict[str, Any]:
        values: list[float] = []
        r_values: list[float] = []
        for case in cases:
            exit_context = case.get("exit_context", {}) if isinstance(case.get("exit_context"), Mapping) else {}
            net = cls._safe_float(exit_context.get("net_realized_profit_usd"))
            if net is None:
                continue
            values.append(net)
            r_value = cls._safe_float(exit_context.get("realized_r_multiple"))
            if r_value is not None:
                r_values.append(r_value)
        wins = [x for x in values if x > 0]
        losses = [x for x in values if x < 0]
        breakeven = len(values) - len(wins) - len(losses)
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        net = sum(values)
        equity = peak = 0.0
        max_dd = current_dd = 0.0
        for value in values:
            equity += value
            peak = max(peak, equity)
            current_dd = peak - equity
            max_dd = max(max_dd, current_dd)
        count = len(values)
        average_win = sum(wins) / len(wins) if wins else None
        average_loss = sum(losses) / len(losses) if losses else None
        expectancy = net / count if count else None
        profit_factor = gross_profit / gross_loss if gross_loss else (gross_profit if wins else None)
        recovery_factor = net / max_dd if max_dd > 0 else (None if count == 0 else net)
        win_rate = len(wins) / count if count else None
        payoff = (average_win / abs(average_loss)) if average_win is not None and average_loss not in (None, 0) else None
        kelly = (win_rate - ((1-win_rate)/payoff)) if win_rate is not None and payoff not in (None, 0) else None
        sharpe = sortino = None
        if len(r_values) >= 2:
            import statistics, math
            mean_r = statistics.mean(r_values)
            stdev = statistics.stdev(r_values)
            sharpe = mean_r / stdev * math.sqrt(len(r_values)) if stdev > 0 else None
            downside = [min(0.0, r) for r in r_values]
            downside_dev = (sum(x*x for x in downside) / len(downside)) ** 0.5
            sortino = mean_r / downside_dev * math.sqrt(len(r_values)) if downside_dev > 0 else None
        return {
            "trade_count": count, "wins": len(wins), "losses": len(losses), "breakeven": breakeven,
            "net_realized_profit_usd": round(net, 2),
            "average_win_usd": round(average_win, 2) if average_win is not None else DATA_UNAVAILABLE,
            "average_loss_usd": round(average_loss, 2) if average_loss is not None else DATA_UNAVAILABLE,
            "win_rate_percent": round(win_rate*100, 2) if win_rate is not None else DATA_UNAVAILABLE,
            "profit_factor": round(profit_factor, 4) if profit_factor is not None else DATA_UNAVAILABLE,
            "expectancy_usd": round(expectancy, 4) if expectancy is not None else DATA_UNAVAILABLE,
            "maximum_drawdown_usd": round(max_dd, 2), "current_drawdown_usd": round(current_dd, 2),
            "recovery_factor": round(recovery_factor, 4) if recovery_factor is not None else DATA_UNAVAILABLE,
            "sharpe_ratio": round(sharpe, 4) if sharpe is not None else DATA_UNAVAILABLE,
            "sortino_ratio": round(sortino, 4) if sortino is not None else DATA_UNAVAILABLE,
            "kelly_fraction": round(kelly, 4) if kelly is not None else DATA_UNAVAILABLE,
            "metric_status": "AVAILABLE" if count else "INSUFFICIENT_ELIGIBLE_CLOSED_TRADES",
        }

    @staticmethod
    def _period_key(timestamp: datetime, period: str) -> str:
        if period == "daily": return timestamp.strftime("%Y-%m-%d")
        if period == "weekly": return f"{timestamp.isocalendar().year}-W{timestamp.isocalendar().week:02d}"
        if period == "monthly": return timestamp.strftime("%Y-%m")
        return timestamp.strftime("%Y")

    def evaluate(self) -> dict[str, Any]:
        account = FinancialIntegrityRuntime(self.root).evaluate()
        cases = self._eligible_closed_cases()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for dimension in ("profile", "pattern", "plan"):
            rows: dict[str, list[dict[str, Any]]] = {}
            for case in cases:
                rows.setdefault(self._case_dimension(case, dimension), []).append(case)
            grouped[f"by_{dimension}"] = [
                {f"{dimension}_id": key, **self._metrics(items)} for key, items in sorted(rows.items())
            ]
        now = _utcnow()
        period_cases: dict[str, list[dict[str, Any]]] = {p: [] for p in self.PERIODS}
        for case in cases:
            exit_context = case.get("exit_context", {}) if isinstance(case.get("exit_context"), Mapping) else {}
            stamp = _parse_time(exit_context.get("close_time") or exit_context.get("closed_at") or exit_context.get("exit_time"))
            if not stamp: continue
            for period in self.PERIODS:
                if self._period_key(stamp, period) == self._period_key(now, period):
                    period_cases[period].append(case)
        return {
            "schema_version": "afip_v1_financial_analytics_certification_v1",
            "generated_at": now.isoformat().replace("+00:00", "Z"),
            "currency": "USD",
            "data_policy": "VERIFIED_ACCOUNT_SNAPSHOTS_AND_ELIGIBLE_NET_OUTCOMES_ONLY",
            "account_snapshot": account,
            "portfolio_performance": self._metrics(cases),
            "period_performance": {period: self._metrics(items) for period, items in period_cases.items()},
            **grouped,
            "affects_trading": False,
            "execution_permission": False,
        }

    def write(self, output: str | Path = "runtime/certification/financial_analytics.json") -> Path:
        path = self.root / output
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.evaluate(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
