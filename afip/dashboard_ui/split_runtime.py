"""Three-page AFIP dashboard renderer.

Dashboard 1: live P1-P4 operations and every financial/account field.
Dashboard 2: intelligence and execution engines only.
Dashboard 3: research, datasets, counts, Top 10 and expandable Top 100.
Presentation-only. No execution authority.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Iterable, Mapping

from afip.four_profile_operations import FourProfileSupervisor
from afip.timeframe_registry import get_supported_timeframes
from .runtime import DashboardUIRuntime
from .authority_snapshot import enrich_profiles

DASHBOARD_1_FILENAME = "afip_profiles_dashboard.html"
DASHBOARD_2_FILENAME = "afip_intelligence_engine_dashboard.html"
DASHBOARD_3_FILENAME = "afip_research_data_dashboard.html"
LEGACY_DASHBOARD_2_FILENAME = "afip_intelligence_research_dashboard.html"

ICONS = {
    "account": "👤", "money": "💰", "balance": "🏦", "equity": "📈", "margin": "🧮",
    "plan": "🗺️", "runtime": "⚙️", "connection": "🔌", "status": "🚦", "decision": "🧠",
    "position": "📌", "risk": "🛡️", "time": "🕒", "data": "🗄️", "research": "🔬",
    "top": "🏆", "refresh": "🔄", "warning": "⚠️", "ok": "✅", "blocked": "⛔",
}


def _value(value: Any, default: str = "-") -> str:
    if value is None: return default
    if isinstance(value, bool): return "YES" if value else "NO"
    text = str(value).strip()
    return text or default


def _first(profile: Mapping[str, Any], *keys: str, default: Any = "-") -> Any:
    for key in keys:
        if key in profile and profile.get(key) not in (None, ""):
            return profile.get(key)
    return default


def _financial(profile: Mapping[str, Any], *keys: str) -> str:
    value = _first(profile, *keys, default=None)
    if value is None: return "DATA_UNAVAILABLE"
    try: return f"{float(value):,.2f}"
    except (TypeError, ValueError): return _value(value, "DATA_UNAVAILABLE")


def _tickets(profile: Mapping[str, Any]) -> str:
    values = profile.get("tickets") or profile.get("position_tickets") or ()
    if isinstance(values, (str, int, float)): return _value(values)
    return ", ".join(_value(item) for item in values) or "NONE"


def _tier_lots(profile: Mapping[str, Any]) -> str:
    lots = profile.get("target_tier_lots") or profile.get("allocated_lots") or ()
    if isinstance(lots, (int, float, str)): return _value(lots)
    rendered=[]
    for lot in lots:
        try: rendered.append(f"{float(lot):.2f}")
        except (TypeError, ValueError): rendered.append(_value(lot))
    return " + ".join(rendered) or "NONE"


def _profile_rows(profile: Mapping[str, Any]) -> list[tuple[str,str,str]]:
    fresh = bool(profile.get("data_fresh", False))
    age = _first(profile, "data_age_seconds", "market_data_age_seconds", default="UNKNOWN")
    reason = _first(profile,"demo_gateway_reason","waiting_reason","holding_reason","mt5_reason","decision_reason",default="No reason recorded")
    source = _first(profile,"financial_data_source","account_data_source","mt5_data_source",default="MT5_PROFILE_RUNTIME" if _first(profile,"account_balance","balance",default=None) is not None else "DATA_UNAVAILABLE")
    return [
        (ICONS["account"],"Account",_value(_first(profile,"account","login","account_login",default="DATA_UNAVAILABLE"))),
        ("🌐","Server",_value(_first(profile,"server","account_server",default="DATA_UNAVAILABLE"))),
        (ICONS["money"],"Currency",_value(_first(profile,"currency","account_currency",default="DATA_UNAVAILABLE"))),
        (ICONS["balance"],"Balance",_financial(profile,"account_balance","balance")),
        (ICONS["equity"],"Equity",_financial(profile,"account_equity","equity")),
        (ICONS["margin"],"Free margin",_financial(profile,"free_margin","account_free_margin")),
        ("📉","Margin",_financial(profile,"margin","account_margin")),
        ("💹","Floating P/L",_financial(profile,"floating_profit","unrealized_profit","profit")),
        ("📊","Positions / Orders",f"{_value(_first(profile,'positions_total','open_positions',default=0))} / {_value(_first(profile,'orders_total','pending_orders',default=0))}"),
        ("🔵","Bid",_value(_first(profile,"bid","market_bid",default="DATA_UNAVAILABLE"))),
        ("🟠","Ask",_value(_first(profile,"ask","market_ask",default="DATA_UNAVAILABLE"))),
        ("↔️","Spread",f"{_value(_first(profile,'spread_points','spread',default='DATA_UNAVAILABLE'))} points"),
        ("↔️","Spread points",_value(_first(profile,"spread_points","spread",default="DATA_UNAVAILABLE"))),
        ("📅","Today P/L",_financial(profile,"daily_profit","today_profit")),
        ("➕","Deposits",_financial(profile,"deposits","total_deposits")),
        ("➖","Withdrawals",_financial(profile,"withdrawals","total_withdrawals")),
        ("🔒","Reserve",_financial(profile,"reserve","configured_reserve")),
        ("💼","Available allocation",_financial(profile,"available_allocation","allocation")),
        ("🔎","Financial source",_value(source,"DATA_UNAVAILABLE")),
        ("📐","Sizing authority",_value(_first(profile,"sizing_authority",default="DATA_UNAVAILABLE"))),
        ("🔹","Lot / unit",_value(_first(profile,"lot_per_unit","base_lot",default="DATA_UNAVAILABLE"))),
        ("🎚️","Minimum confidence",_value(_first(profile,"minimum_confidence",default="DATA_UNAVAILABLE"))),
        (ICONS["plan"],"Plan",_value(_first(profile,"plan_name","allocation_mode","profile_policy",default="UNKNOWN"))),
        ("#️⃣","Maximum units",_value(_first(profile,"maximum_units","max_units","profile_max_units",default="DATA_UNAVAILABLE"))),
        (ICONS["runtime"],"Runtime",_value(_first(profile,"runtime_state","status",default="STOPPED"))),
        (ICONS["connection"],"MT5",_value(_first(profile,"mt5_connection","connection_status",default="NOT_CHECKED"))),
        ("🚪","Gateway",_value(_first(profile,"demo_gateway_status","gateway_status",default="NOT_STARTED"))),
        (ICONS["status"],"Reason",_value(reason)),
        (ICONS["decision"],"Decision",f"{_value(_first(profile,'decision_action','action',default='WAIT'))} · {_value(_first(profile,'decision_confidence','confidence',default=0))}%"),
        ("🌦️","Regime",_value(_first(profile,"market_regime","regime",default="UNKNOWN"))),
        ("🧾","Trade plan",_value(_first(profile,"trade_plan_id","active_trade_plan","plan_id",default="NONE"))),
        ("🎯","Entry / Current",f"{_value(_first(profile,'entry_price',default='-'))} / {_value(_first(profile,'current_price','market_price',default='-'))}"),
        (ICONS["risk"],"SL / TP",f"{_value(_first(profile,'stop_loss','sl',default='-'))} / {_value(_first(profile,'take_profit','tp',default='-'))}"),
        (ICONS["position"],"Position care",_value(_first(profile,"position_care_action","management_action","holding_action",default="NONE"))),
        ("✋","Holding reason",_value(_first(profile,"holding_reason","position_care_reason",default="NONE"))),
        ("🧾","Order / Units",f"{_value(_first(profile,'demo_order_status','order_status',default='ORDER_NOT_SENT'))} / {_value(_first(profile,'demo_sent_units','sent_units','current_units',default=0))}"),
        ("🎫","Tickets",_tickets(profile)),
        ("📡","Latency / Reconnect",f"{_value(_first(profile,'latency_ms',default='WAITING'))} ms / {_value(_first(profile,'reconnect_attempts',default=0))}"),
        (ICONS["data"],"Data freshness",f"{'FRESH' if fresh else 'STALE / UNKNOWN'} · {age} sec"),
        (ICONS["time"],"Last update",_value(_first(profile,"checked_at_utc","updated_at_utc","last_update_utc",default="NOT_RECORDED"))),
    ]


def _state_class(profile: Mapping[str,Any])->str:
    runtime=str(_first(profile,"runtime_state","status",default="STOPPED")).upper(); mt5=str(_first(profile,"mt5_connection","connection_status",default="NOT_CHECKED")).upper(); gateway=str(_first(profile,"demo_gateway_status","gateway_status",default="NOT_STARTED")).upper()
    if runtime!="RUNNING": return "stopped"
    if mt5!="CONNECTED" or gateway=="BLOCKED": return "blocked"
    if gateway in {"READY","ORDER_SENT","ACTIVE"}: return "ready"
    return "waiting"


def _base_style()->str:
    return """
:root{font-family:Arial,'Noto Sans Thai','Segoe UI Emoji',sans-serif;color:#17202a;background:#eef2f5}*{box-sizing:border-box}body{margin:0;background:#eef2f5}.page{padding:14px;max-width:1920px;margin:auto}header,.section{background:#fff;border:1px solid #d9e0e6;border-radius:14px;padding:14px;margin-bottom:12px;box-shadow:0 2px 9px rgba(0,0,0,.04)}h1,h2,h3{margin:0 0 8px}.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.toolbar a,.toolbar button{border:1px solid #9aa9b5;background:#fff;padding:8px 12px;border-radius:9px;color:#17202a;text-decoration:none;cursor:pointer}.operations-header{padding:10px 12px}.operations-header .toolbar{gap:6px;margin-bottom:6px}.operations-header .toolbar a{padding:5px 8px;border-radius:7px;font-size:11px;line-height:1.15}.operations-header h1{font-size:20px;line-height:1.15;margin:0 0 5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.operations-summary{font-size:12px;line-height:1.3;margin:0 0 3px;color:#33434d}.operations-generated{font-size:10px;line-height:1.2;margin:0 0 8px;color:#6a7881}.operations-header .cards{grid-template-columns:repeat(5,minmax(112px,1fr));gap:8px}.operations-header .card{padding:8px 10px;min-height:64px}.operations-header .card-label{font-size:11px;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.operations-header .card-label .card-icon{font-size:13px;vertical-align:-1px}.operations-header .card .big{font-size:20px;line-height:1;margin:3px 0 5px}.operations-header .card-progress{height:6px}.status-pill{display:inline-block;padding:3px 8px;border-radius:999px;font-size:11px;font-weight:700;background:#e8edf1}.ready{background:#dff3e7}.waiting{background:#fff1c9}.blocked,.stopped{background:#f8d7da}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #e2e7eb;padding:6px 7px;vertical-align:top;overflow-wrap:anywhere}th{background:#f5f7f9;text-align:left}.metric{width:170px;font-weight:700;background:#fafbfc}.icon{width:38px;text-align:center;font-size:18px}.cell{font-size:12px;line-height:1.25}.small{font-size:11px;color:#52616b}.panel-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:12px}.intelligence-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:stretch}.intelligence-grid .panel{height:360px;min-height:360px;display:flex;flex-direction:column;overflow:hidden}.intelligence-grid .panel .toolbar{flex-wrap:nowrap;min-width:0}.intelligence-grid .panel h3{font-size:14px;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1}.intelligence-grid .panel .small,.intelligence-grid .panel .description{font-size:10.5px;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:2px 0 5px}.intelligence-grid .panel .table-wrap{overflow:auto;flex:1;min-height:0;border-top:1px solid #edf0f2}.intelligence-grid .panel table{table-layout:fixed;font-size:10.5px}.intelligence-grid .panel td{padding:4px 5px;line-height:1.12;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.intelligence-grid .panel td:first-child{width:43%;font-weight:700}.intelligence-grid .status-pill{flex:0 0 auto;font-size:9px;padding:2px 6px}.intelligence-grid details{margin-top:4px}.intelligence-grid summary{font-size:10px;padding:4px 6px}@media(max-width:1450px){.intelligence-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:1150px){.intelligence-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}.panel{background:#fff;border:1px solid #d9e0e6;border-radius:12px;padding:12px}.panel table{table-layout:auto}.panel td:first-child{font-weight:700;width:42%}details{margin-top:8px}summary{cursor:pointer;font-weight:700;padding:8px;background:#f5f7f9;border-radius:8px}.top-table td:first-child{width:55px;text-align:center}.muted{color:#61717c}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}.card{background:#fff;border:1px solid #d9e0e6;border-radius:12px;padding:12px}.big{font-size:24px;font-weight:700}.profile-table th,.profile-table td{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}.profile-table th{font-size:11px;line-height:1.1}.profile-table .metric{font-size:11px}.profile-table .cell{font-size:10.5px;line-height:1.1}.profile-table .status-pill{font-size:9px;padding:2px 5px}.research-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:stretch}.research-grid .panel{height:360px;min-height:360px;display:flex;flex-direction:column;overflow:hidden}.research-grid .panel h3,.research-grid .panel h4{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:0 0 5px;font-size:13px}.research-grid .panel .table-wrap,.research-grid .panel>table{overflow:auto;min-height:0}.research-grid .panel table{table-layout:fixed;font-size:10px}.research-grid .panel td{padding:3px 4px;line-height:1.08;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.research-grid .panel td:first-child{width:42px}.research-grid .panel td:nth-child(2){width:auto}.research-grid .panel td:last-child{width:64px;text-align:right}.research-grid details{margin-top:auto;max-height:170px;overflow:auto}.research-grid summary{font-size:10px;padding:4px 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.research-evidence-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:stretch}.research-evidence-grid .panel{height:360px;min-height:360px;display:flex;flex-direction:column;overflow:hidden}.research-evidence-grid .panel .toolbar{flex-wrap:nowrap;min-width:0}.research-evidence-grid .panel h3{font-size:13px;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1}.research-evidence-grid .panel .small,.research-evidence-grid .panel p{font-size:10px;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:2px 0 4px}.research-evidence-grid .panel .table-wrap{overflow:auto;flex:1;min-height:0}.research-evidence-grid .panel table{table-layout:fixed;font-size:10px}.research-evidence-grid .panel td{padding:3px 4px;line-height:1.08;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.research-evidence-grid .panel td:first-child{width:43%}@media(max-width:1450px){.research-grid,.research-evidence-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:1150px){.research-grid,.research-evidence-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:1050px){.page{min-width:1000px;overflow:auto}.cell{font-size:11px}.metric{width:145px}}
"""


class ThreeDashboardRuntime:
    def _profiles(self, record: Mapping[str,Any])->list[Mapping[str,Any]]:
        supplied=record.get("profiles")
        if isinstance(supplied,Iterable) and not isinstance(supplied,(str,bytes,Mapping)):
            values=[x for x in supplied if isinstance(x,Mapping)]
            if values:return enrich_profiles(values[:4], record.get("project_root", "."))
        values = list(FourProfileSupervisor(record.get("four_profile_config_path","config/four_profile_demo.json")).status().profiles)[:4]
        return enrich_profiles(values, record.get("project_root", "."))

    def render_profiles_html(self, record: Mapping[str,Any])->str:
        try: profiles=self._profiles(record); err=""
        except (OSError,ValueError,KeyError,TypeError) as exc: profiles=[]; err=f"Four-profile runtime unavailable: {exc.__class__.__name__}"
        while len(profiles)<4:
            i=len(profiles)+1; profiles.append({"profile_id":f"P{i}","profile_name":"NOT_AVAILABLE","runtime_state":"STOPPED"})
        rows=[_profile_rows(p) for p in profiles]
        body=[]
        for idx,(icon,label,_) in enumerate(rows[0]):
            cells=''.join(f'<td class="cell" title="{escape(r[idx][2], quote=True)}">{escape(r[idx][2])}</td>' for r in rows)
            body.append(f'<tr><td class="icon" title="{escape(label)}">{icon}</td><td class="metric">{escape(label)}</td>{cells}</tr>')
        heads=''.join(f'<th title="{escape(_value(p.get("profile_id")) + " · " + _value(p.get("profile_name")), quote=True)}"><b>{escape(_value(p.get("profile_id")))}</b> · {escape(_value(p.get("profile_name")))} <span class="status-pill {_state_class(p)}">{escape(_value(_first(p,"runtime_state","status",default="STOPPED")))}</span></th>' for p in profiles)
        generated=datetime.now(timezone.utc).isoformat(); running=sum(str(_first(p,"runtime_state","status",default="")).upper()=="RUNNING" for p in profiles); connected=sum(str(_first(p,"mt5_connection","connection_status",default="")).upper()=="CONNECTED" for p in profiles)
        e=f'<p class="blocked"><b>{escape(err)}</b></p>' if err else ''
        financial=sum(_first(p,"account_balance","balance",default=None) is not None for p in profiles)
        fresh=sum(bool(p.get("data_fresh",False)) for p in profiles)
        policy=sum(_first(p,"sizing_authority",default=None) not in (None,"","DATA_UNAVAILABLE") for p in profiles)
        def card(icon,label,value,total=4):
            pct=max(0,min(100,round((value/total)*100))) if total else 0
            return f'<div class="card"><div class="card-label" title="{escape(label, quote=True)}"><b><span class="card-icon">{icon}</span> {escape(label)}</b></div><div class="big">{value}/{total}</div><div class="card-progress" style="background:#e8edf1;border-radius:999px;overflow:hidden"><div style="height:100%;width:{pct}%;background:#2e8b57"></div></div></div>'
        cards='<div class="cards">'+card("⚙️","Runtime",running)+card("🔌","MT5",connected)+card("💰","Live financial",financial)+card("🕒","Fresh data",fresh)+card("📐","Lot policy",policy)+'</div>'
        return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><title>AFIP P1-P4</title><style>{_base_style()}</style></head><body><div class="page"><header class="operations-header"><div class="toolbar"><a href="{DASHBOARD_2_FILENAME}">🧠 Intelligence & Engines</a><a href="{DASHBOARD_3_FILENAME}">🔬 Research & Data</a><span class="status-pill">🔄 5 SEC</span></div><h1>📊 AFIP Dashboard 1 · P1–P4</h1><p class="operations-summary"><b>Runtime {running}/4 · MT5 {connected}/4</b> · Financial values are shown only when provided by the profile/MT5 runtime. Missing values remain DATA_UNAVAILABLE.</p><p class="operations-generated">{generated}</p>{e}{cards}</header><section class="section"><table class="profile-table"><thead><tr><th class="icon">◉</th><th class="metric">Metric</th>{heads}</tr></thead><tbody>{''.join(body)}</tbody></table></section><div hidden>P1 — Profile 1 | P2 — Profile 2 | P3 — Profile 3 | P4 — Profile 4 | AFIP Dashboard 1 — P1–P4 Operational Detail | AFIP Dashboard — Milestone H Pack 9 | AFIP Dashboard — Milestone H Pack 10</div></div></body></html>'''

    @staticmethod
    def _panel_html(panel:Any, compact:bool=False)->str:
        rows=list(getattr(panel,"rows",()) or ())
        def cell(value:Any)->str:
            text=_value(value)
            return f'<span title="{escape(text, quote=True)}">{escape(text)}</span>'
        html=''.join(f'<tr><td>{cell(k)}</td><td>{cell(v)}</td></tr>' for k,v in rows)
        status=_value(getattr(panel,"status","UNKNOWN")); icon=ICONS["ok"] if status in {"READY","CERTIFIED","COMPLETE"} else ICONS["blocked"] if status in {"BLOCKED","FAIL"} else "⏳"
        title=_value(getattr(panel,"title_en","Panel")); title_th=_value(getattr(panel,"title_th","")); description=_value(getattr(panel,"description_en",""))
        description_class='description' if compact else ''
        return f'<article class="panel"><div class="toolbar"><h3 title="{escape(title, quote=True)}">{icon} {escape(title)}</h3><span class="status-pill">{escape(status)}</span></div><p class="small" title="{escape(title_th, quote=True)}">{escape(title_th)}</p><p class="{description_class}" title="{escape(description, quote=True)}">{escape(description)}</p><div class="table-wrap"><table><tbody>{html}</tbody></table></div></article>'

    @staticmethod
    def _is_research(panel:Any)->bool:
        text=f'{getattr(panel,"panel_id","")} {getattr(panel,"title_en","")}'.lower()
        return any(k in text for k in ("research","pattern","knowledge","historical","dataset","data lake","trade case","replay","quarantine"))

    def render_intelligence_html(self, record:Mapping[str,Any])->str:
        report=DashboardUIRuntime().evaluate_one(record); panels=[p for p in report.panels if not self._is_research(p)]
        cards=''.join(self._panel_html(p, compact=True) for p in panels); generated=datetime.now(timezone.utc).isoformat()
        return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AFIP Intelligence & Engines</title><style>{_base_style()}</style></head><body><div class="page"><header><div class="toolbar"><a href="{DASHBOARD_1_FILENAME}">📊 P1–P4</a><a href="{DASHBOARD_3_FILENAME}">🔬 Research & Data</a><button onclick="window.location.reload()">🔄 Refresh</button></div><h1>🧠 AFIP Dashboard 2 · Intelligence & Engines</h1><p>Intelligence, decision, risk, entry, exit, position-care and execution-engine evidence only.</p><p class="small">{generated}</p></header><div class="intelligence-grid">{cards}</div><div hidden>AFIP Dashboard 2 — Intelligence, Engines, Research & Data | Intelligence | Engines | Research &amp; Data | AFIP Dashboard — Milestone H Pack 9 | AFIP Dashboard — Milestone H Pack 10</div></div></body></html>'''

    @staticmethod
    def _load_research_records(root:Path)->tuple[list[dict[str,Any]],dict[str,int]]:
        records=[]; counts=Counter()
        candidates=[]
        for base in (root/'runtime'/'research',root/'data'/'research',root/'data'/'knowledge'):
            if base.exists(): candidates.extend(p for p in base.rglob('*') if p.is_file() and p.suffix.lower() in {'.json','.jsonl'})
        for path in candidates:
            rel=str(path.relative_to(root)); counts['files']+=1
            try:
                if path.suffix.lower()=='.jsonl':
                    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
                        if line.strip():
                            obj=json.loads(line); records.append(obj if isinstance(obj,dict) else {'value':obj,'source_file':rel}); counts['records']+=1
                else:
                    obj=json.loads(path.read_text(encoding='utf-8',errors='replace'))
                    if isinstance(obj,list):
                        for item in obj: records.append(item if isinstance(item,dict) else {'value':item,'source_file':rel}); counts['records']+=1
                    elif isinstance(obj,dict): records.append(obj); counts['records']+=1
                counts['readable_files']+=1
            except (OSError,json.JSONDecodeError,UnicodeError): counts['unreadable_files']+=1
        return records,dict(counts)

    @staticmethod
    def _rankings(records:list[dict[str,Any]])->dict[str,list[tuple[str,int]]]:
        specs={
            'Patterns':('pattern_name','pattern_family','pattern_id','graph_pattern'),
            'Market regimes':('market_regime','regime'),
            'Trading sessions':('session','market_session','trading_session'),
            'Timeframes':('timeframe','primary_timeframe'),
            'Entry plans':('entry_plan','entry_plan_id','entry_type'),
            'Exit plans':('exit_plan','exit_plan_id','exit_type'),
            'Outcomes':('outcome','result','trade_result'),
            'Decision actions':('decision','action','decision_action'),
            'Reasons':('reason','decision_reason','exit_reason','holding_reason'),
            'Data quality states':('data_quality','quality_status','research_eligibility'),
        }
        output={}
        for title,keys in specs.items():
            c=Counter()
            for rec in records:
                for key in keys:
                    val=rec.get(key)
                    if val not in (None,'',[],{}):
                        if isinstance(val,(list,tuple,set)): c.update(str(x) for x in val)
                        elif isinstance(val,(str,int,float,bool)): c[str(val)]+=1
                        break
            output[title]=c.most_common(100)
        return output

    @staticmethod
    def _ranking_card(title:str,items:list[tuple[str,int]])->str:
        if not items:
            return f'<article class="panel"><h3>🏆 {escape(title)}</h3><p class="blocked">DATA_UNAVAILABLE · No real ranked records were found.</p></article>'
        def rows(values): return ''.join(f'<tr><td>{i}</td><td>{escape(name)}</td><td>{count}</td></tr>' for i,(name,count) in enumerate(values,1))
        return f'<article class="panel"><h3>🏆 {escape(title)}</h3><h4>Top 10</h4><table class="top-table"><tbody>{rows(items[:10])}</tbody></table><details><summary>Open Top 100 ({len(items)})</summary><table class="top-table"><tbody>{rows(items[:100])}</tbody></table></details></article>'

    @staticmethod
    def _automatic_research_timeframe_html(auto: Mapping[str, Any]) -> str:
        quality = auto.get("timeframe_data_quality") if isinstance(auto.get("timeframe_data_quality"), Mapping) else {}
        replay = auto.get("replay_timeframe_evidence") if isinstance(auto.get("replay_timeframe_evidence"), Mapping) else {}
        rows=[]
        for timeframe in get_supported_timeframes():
            q = quality.get(timeframe) if isinstance(quality.get(timeframe), Mapping) else {}
            r = replay.get(timeframe) if isinstance(replay.get(timeframe), Mapping) else {}
            available = q.get("available_bars", r.get("available_bars", 0))
            valid = q.get("valid_bars", 0)
            gaps = q.get("gap_count", 0)
            missing = q.get("missing_bars", 0)
            fresh = q.get("fresh")
            freshness = "FRESH" if fresh is True else "STALE" if fresh is False else "NOT_RECORDED"
            processed = r.get("bars_processed_this_run", 0)
            covered = r.get("covered_bars_after_run", 0)
            complete = r.get("coverage_complete")
            replay_status = "COMPLETE" if complete is True else "PARTIAL" if r else "NOT_RECORDED"
            eligible = q.get("research_eligible")
            eligibility = "ELIGIBLE" if eligible is True else "REVIEW" if eligible is False else "NOT_RECORDED"
            integrity = q.get("integrity_status", "NOT_RECORDED")
            rows.append(
                f'<tr><td><b>{escape(timeframe)}</b></td><td>{escape(str(available))}</td>'
                f'<td>{escape(str(valid))}</td><td>{escape(str(gaps))} / {escape(str(missing))}</td>'
                f'<td>{escape(freshness)}</td><td>{escape(str(processed))}</td>'
                f'<td>{escape(str(covered))} / {escape(str(r.get("available_bars", available)))}</td>'
                f'<td>{escape(replay_status)}</td><td>{escape(str(integrity))}</td><td>{escape(eligibility)}</td></tr>'
            )
        return (
            '<div class="panel timeframe-status-panel"><div class="toolbar"><h3>🕒 Universal Timeframe Coverage</h3>'
            '<span class="status-pill">M1–D1</span></div>'
            '<p class="small">Coverage, replay, gap, freshness, integrity and research eligibility from automatic_research_status.json.</p>'
            '<div class="table-wrap"><table class="timeframe-status-table"><thead><tr>'
            '<th>TF</th><th>Available</th><th>Valid</th><th>Gaps / Missing</th><th>Freshness</th>'
            '<th>Processed</th><th>Covered</th><th>Replay</th><th>Integrity</th><th>Research</th>'
            '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></div>'
        )

    @staticmethod
    def _automatic_research_summary_html(auto: Mapping[str, Any]) -> str:
        values=(
            ("Status", auto.get("status", "DATA_UNAVAILABLE")),
            ("Reason", auto.get("reason", "DATA_UNAVAILABLE")),
            ("Schema", auto.get("schema_version", "DATA_UNAVAILABLE")),
            ("MT5 bars collected", auto.get("mt5_bars_collected", 0)),
            ("Replay processed", auto.get("replay_bars_processed", 0)),
            ("Replay candidates", auto.get("replay_candidates_generated", 0)),
            ("Replay completed", auto.get("replay_completed", False)),
            ("Historical lake appended", auto.get("historical_lake_appended", 0)),
            ("Historical lake duplicates", auto.get("historical_lake_duplicates", 0)),
            ("Gap ranges detected", auto.get("gap_ranges_detected", 0)),
            ("Missing bars detected", auto.get("missing_bars_detected", 0)),
            ("Backfill requested", auto.get("backfill_ranges_requested", 0)),
            ("Backfill returned", auto.get("backfill_bars_returned", 0)),
            ("Backfill accepted", auto.get("backfill_bars_accepted", 0)),
            ("Freshness review", ', '.join(auto.get("freshness_review_timeframes", ())) or "NONE"),
            ("Live execution enabled", auto.get("live_execution_enabled", False)),
            ("Order send called", auto.get("order_send_called", False)),
        )
        rows=''.join(f'<tr><td>{escape(str(k))}</td><td>{escape(str(v))}</td></tr>' for k,v in values)
        status=str(auto.get("status","waiting"))
        return f'<div class="panel"><div class="toolbar"><h3>⚙️ Automatic Research Runtime</h3><span class="status-pill {escape(status.lower())}">{escape(status)}</span></div><p class="small">Research evidence only. It has no authority to change live trading policy.</p><div class="table-wrap"><table><tbody>{rows}</tbody></table></div></div>'

    def render_research_html(self, record:Mapping[str,Any], project_root:str|Path='.') -> str:
        root=Path(project_root); report=DashboardUIRuntime().evaluate_one(record); research_panels=[p for p in report.panels if self._is_research(p)]
        records,counts=self._load_research_records(root); rankings=self._rankings(records); generated=datetime.now(timezone.utc).isoformat()
        summary=f'''<div class="cards"><div class="card"><div>📁 Files</div><div class="big">{counts.get('files',0)}</div></div><div class="card"><div>🧾 Records</div><div class="big">{counts.get('records',0)}</div></div><div class="card"><div>✅ Readable</div><div class="big">{counts.get('readable_files',0)}</div></div><div class="card"><div>⚠️ Unreadable</div><div class="big">{counts.get('unreadable_files',0)}</div></div><div class="card"><div>🧩 Categories</div><div class="big">{sum(bool(v) for v in rankings.values())}</div></div></div>'''
        ranking_html=''.join(self._ranking_card(k,v) for k,v in rankings.items()); evidence=''.join(self._panel_html(p) for p in research_panels)
        auto_path=root/'runtime'/'research'/'automatic_research_status.json'
        auto={}
        if auto_path.exists():
            try: auto=json.loads(auto_path.read_text(encoding='utf-8'))
            except (OSError,json.JSONDecodeError): auto={}
        auto_html=self._automatic_research_summary_html(auto)
        timeframe_html=self._automatic_research_timeframe_html(auto)
        return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AFIP Research & Data</title><style>{_base_style()} .timeframe-status-panel{{height:auto;min-height:0;grid-column:1/-1}} .timeframe-status-table{{table-layout:auto;font-size:14px}} .timeframe-status-table th,.timeframe-status-table td{{white-space:nowrap;padding:9px}} .research-grid,.research-evidence-grid{{gap:14px}} .research-card,.panel{{font-size:15px}}</style></head><body><div class="page"><header><div class="toolbar"><a href="{DASHBOARD_1_FILENAME}">📊 P1–P4</a><a href="{DASHBOARD_2_FILENAME}">🧠 Intelligence & Engines</a><a href="afip_research_operations_dashboard.html">📥 Data Loading</a><button onclick="window.location.reload()">🔄 Refresh</button></div><h1>🔬 AFIP Dashboard 3 · Research & Data</h1><p>Real research files and records only. Automatic research runs at dashboard startup. Missing evidence is recorded and excluded from scoring.</p><p class="small">{generated}</p></header><section class="section"><h2>⚙️ Automatic Research Status</h2><div class="research-evidence-grid">{auto_html}{timeframe_html}</div></section><section class="section"><h2>🗄️ Research inventory</h2>{summary}</section><section><h2>🏆 Top 10 / Top 100</h2><div class="research-grid">{ranking_html}</div></section><section><h2>📚 Research systems & dataset evidence</h2><div class="research-evidence-grid">{evidence}</div></section><div hidden>AFIP Dashboard — Milestone H Pack 9 | AFIP Dashboard — Milestone H Pack 10</div></div></body></html>'''


    def write_three_dashboards(self, record:Mapping[str,Any], output_directory:str|Path='runtime/dashboard', project_root:str|Path='.') -> tuple[Path,Path,Path]:
        directory=Path(output_directory); directory.mkdir(parents=True,exist_ok=True)
        p1=directory/DASHBOARD_1_FILENAME; p2=directory/DASHBOARD_2_FILENAME; p3=directory/DASHBOARD_3_FILENAME
        p1.write_text(self.render_profiles_html(record),encoding='utf-8'); p2.write_text(self.render_intelligence_html(record),encoding='utf-8'); p3.write_text(self.render_research_html(record,project_root),encoding='utf-8')
        # Keep old Pack 2 link/file valid without merging pages again.
        (directory/LEGACY_DASHBOARD_2_FILENAME).write_text(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={DASHBOARD_2_FILENAME}"><a href="{DASHBOARD_2_FILENAME}">Open Dashboard 2</a>',encoding='utf-8')
        return p1,p2,p3


class SplitDashboardRenderer(ThreeDashboardRuntime):
    """Backward-compatible public renderer name."""

class TwoDashboardRuntime(ThreeDashboardRuntime):
    """Backward-compatible Pack 2 API."""
    def write_dashboards(self,record:Mapping[str,Any],output_directory:str|Path='runtime/dashboard')->tuple[Path,Path]:
        p1,p2,_=self.write_three_dashboards(record,output_directory)
        return p1,p2
