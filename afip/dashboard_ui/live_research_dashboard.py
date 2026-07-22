"""AFIP unified four-page live dashboard (presentation only)."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Mapping

TIMEFRAMES=("M1","M5","M15","M30","H1","H4","D1")
OLD_DASHBOARDS=(
 "afip_profiles_dashboard.html","afip_intelligence_engine_dashboard.html",
 "afip_research_data_dashboard.html","afip_research_operations_dashboard.html",
 "afip_intelligence_research_dashboard.html","afip_cross_market_intelligence_dashboard.html",
)

def _load(path:Path)->dict[str,Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else {}
    except (OSError,json.JSONDecodeError,UnicodeError): return {}

def _v(value:Any)->str:
    if value is None or value=="": return "DATA_UNAVAILABLE"
    if isinstance(value,bool): return "YES" if value else "NO"
    return str(value)

def _card(label:str,value:Any,detail:str="")->str:
    return f'<div class="card"><div class="label">{escape(label)}</div><div class="value">{escape(_v(value))}</div><div class="detail">{escape(detail)}</div></div>'

def _recent_files(root:Path)->list[tuple[str,int,str]]:
    candidates=[]
    for base in (root/"runtime"/"research",root/"runtime"/"dashboard"):
        if not base.exists(): continue
        for p in base.rglob("*"):
            if p.is_file() and not p.name.endswith(".tmp"):
                try: candidates.append((str(p.relative_to(root)),p.stat().st_size,datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()))
                except OSError: pass
    return sorted(candidates,key=lambda x:x[2],reverse=True)[:25]

def build(project_root:str|Path=".", output:str|Path="runtime/dashboard/afip_dashboard.html")->Path:
    root=Path(project_root).resolve(); out=root/Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    auto=_load(root/"runtime"/"research"/"automatic_research_status.json")
    continuous=_load(root/"runtime"/"research"/"continuous_research_status.json")
    cross=_load(root/"runtime"/"research"/"cross_market"/"latest.json")
    evidence=auto.get("replay_timeframe_evidence") or {}
    quality=auto.get("timeframe_data_quality") or {}
    tf_rows=[]
    for tf in TIMEFRAMES:
        r=evidence.get(tf,{}) if isinstance(evidence,Mapping) else {}; q=quality.get(tf,{}) if isinstance(quality,Mapping) else {}
        available=r.get("available_bars", q.get("total_bars", auto.get("current_timeframe_available_bars") if auto.get("current_timeframe")==tf else 0))
        processed=r.get("bars_processed_this_run", auto.get("current_timeframe_processed") if auto.get("current_timeframe")==tf else 0)
        covered=r.get("covered_bars_after_run", auto.get("current_timeframe_covered") if auto.get("current_timeframe")==tf else 0)
        status="ACTIVE" if auto.get("current_timeframe")==tf and auto.get("status")=="RUNNING" else ("COMPLETE" if r.get("coverage_complete") else "WAITING")
        tf_rows.append(f'<tr><td><b>{tf}</b></td><td>{_v(available)}</td><td>{_v(processed)}</td><td>{_v(covered)}</td><td>{_v(q.get("gap_count",0))}</td><td>{_v(q.get("missing_bars",0))}</td><td><span class="pill {status.lower()}">{status}</span></td></tr>')
    recent=''.join(f'<tr><td>{escape(n)}</td><td>{s:,}</td><td>{escape(t)}</td></tr>' for n,s,t in _recent_files(root))
    cards=''.join((
      _card("Runtime",auto.get("status","NOT_STARTED"),auto.get("stage","")),
      _card("Current stage",auto.get("stage","DATA_UNAVAILABLE"),auto.get("reason","")),
      _card("Current timeframe",auto.get("current_timeframe","WAITING")),
      _card("MT5 bars",auto.get("mt5_bars_collected",0)),
      _card("Lake appended",auto.get("historical_lake_appended",0)),
      _card("Lake duplicates",auto.get("historical_lake_duplicates",0)),
      _card("Replay processed",auto.get("replay_bars_processed",0)),
      _card("Candidates",auto.get("replay_candidates_generated",0)),
      _card("Gaps",auto.get("gap_ranges_detected",0)),
      _card("Missing bars",auto.get("missing_bars_detected",0)),
      _card("Last heartbeat",auto.get("updated_at_utc",auto.get("completed_at_utc","NOT_RECORDED"))),
      _card("Execution authority","DISABLED","Research dashboard only"),
    ))
    generated=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    html=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="10"><title>AFIP Unified Dashboard</title><style>
body{{margin:0;font-family:Arial,"Noto Sans Thai",sans-serif;background:#eef2f5;color:#17202a;font-size:16px}}header{{position:sticky;top:0;background:#14213d;color:white;padding:16px 22px;z-index:5}}h1{{margin:0 0 6px;font-size:28px}}nav{{display:flex;gap:8px;flex-wrap:wrap}}nav button{{font-size:16px;padding:9px 15px;border-radius:9px;border:0;cursor:pointer}}main{{padding:16px;max-width:1900px;margin:auto}}.page{{display:none}}.page.active{{display:block}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.card,.panel{{background:white;border:1px solid #d8e0e7;border-radius:14px;padding:15px;margin-bottom:12px}}.label{{font-weight:700;color:#52616b}}.value{{font-size:27px;font-weight:800;margin:7px 0}}.detail{{font-size:13px;overflow-wrap:anywhere}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{border:1px solid #dfe5ea;padding:9px;text-align:left}}th{{background:#f4f6f8}}.pill{{padding:4px 9px;border-radius:999px;font-weight:700}}.active,.running{{background:#dff3e7}}.complete,.ready{{background:#dbeafe}}.waiting{{background:#fff1c9}}.bad{{background:#f8d7da}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:14px}}.notice{{font-size:17px;background:#fff1c9;border-left:6px solid #e0a800;padding:12px}}
</style></head><body><header><h1>AFIP Unified Production Dashboard · 4 Pages</h1><nav><button onclick="show('operations')">1 Operations</button><button onclick="show('intelligence')">2 Intelligence</button><button onclick="show('research')">3 Research & Ranking</button><button onclick="show('loading')">4 Data Loading</button></nav><div>Auto refresh 10s · Generated {escape(generated)}</div></header><main>
<section id="operations" class="page"><div class="panel"><h2>Operations</h2><p>Production account and order panels remain sourced from AFIP runtime. This hotfix does not change execution.</p><pre>{escape(json.dumps(continuous,indent=2,ensure_ascii=False)[:12000])}</pre></div></section>
<section id="intelligence" class="page"><div class="panel"><h2>Intelligence</h2><p>Read-only evidence. Single Intelligence authority will be handled in the final Execution Pack.</p><pre>{escape(json.dumps(cross,indent=2,ensure_ascii=False)[:12000])}</pre></div></section>
<section id="research" class="page"><div class="panel"><h2>Research & Ranking</h2><p>Research evidence, candidates and category ranking inputs.</p>{cards}<pre>{escape(json.dumps(auto.get('ranking',auto.get('research_rankings',{})),indent=2,ensure_ascii=False)[:16000])}</pre></div></section>
<section id="loading" class="page active"><div class="notice"><b>Live interpretation:</b> RUNNING is valid only when heartbeat/file activity changes. The collector currently running uses the old code, so detailed per-timeframe heartbeat begins after the patched collector is restarted.</div><div class="cards">{cards}</div><div class="panel"><h2>M1–D1 Replay and Data Quality</h2><table><thead><tr><th>TF</th><th>Available</th><th>Processed run</th><th>Covered</th><th>Gaps</th><th>Missing</th><th>Status</th></tr></thead><tbody>{''.join(tf_rows)}</tbody></table></div><div class="panel"><h2>Latest Runtime File Activity</h2><table><thead><tr><th>File</th><th>Bytes</th><th>Last write UTC</th></tr></thead><tbody>{recent}</tbody></table></div></section>
</main><script>function show(id){{document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');localStorage.setItem('afipPage',id)}}show(localStorage.getItem('afipPage')||'loading')</script></body></html>'''
    out.write_text(html,encoding="utf-8")
    for name in OLD_DASHBOARDS:
        p=out.parent/name
        if p.exists(): p.unlink()
    return out
