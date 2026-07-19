"""Cross-market and integrity dashboard for Phase U Pack 3.4.9."""
from __future__ import annotations
import json
from html import escape
from pathlib import Path
from typing import Any

DATA_UNAVAILABLE="DATA_UNAVAILABLE"
FILENAME="afip_cross_market_intelligence_dashboard.html"

def _load(path:Path)->dict[str,Any]:
    try:
        v=json.loads(path.read_text(encoding="utf-8")); return v if isinstance(v,dict) else {}
    except Exception:return {}
def _v(v:Any)->str:
    if v in (None,""):return DATA_UNAVAILABLE
    return str(v)
def _status_class(v:Any)->str:
    s=str(v).upper(); return "ok" if s in {"VERIFIED","CONNECTED","FRESH"} else "warn" if s in {"STALE","RESEARCH_ONLY","UNKNOWN"} else "bad"

def render_cross_market_dashboard(project_root:str|Path=".")->str:
    root=Path(project_root)
    financial=_load(root/"runtime/certification/financial_integrity.json")
    intelligence=_load(root/"runtime/certification/intelligence_sources.json")
    cross=_load(root/"runtime/research/cross_market/latest.json")
    profiles=financial.get("profiles",[]) if isinstance(financial.get("profiles"),list) else []
    financial_rows="".join(f"<tr><td>{escape(_v(p.get('profile_id')))}</td><td class='{_status_class(p.get('status'))}'>{escape(_v(p.get('status')))}</td><td>{escape(_v(p.get('data_source')))}</td><td>{escape(_v(p.get('balance')))}</td><td>{escape(_v(p.get('equity')))}</td><td>{escape(_v(p.get('available_allocation')))}</td><td>{escape(_v(p.get('last_update')))}</td><td>{escape(_v(p.get('data_age_seconds')))}</td><td>{escape(_v(p.get('data_freshness')))}</td><td>{escape(_v(p.get('retry_status')))}</td><td>{escape(_v(p.get('connection_status')))}</td></tr>" for p in profiles) or '<tr><td colspan="11">DATA_UNAVAILABLE</td></tr>'
    intel_rows="".join(f"<tr><td>{escape(_v(s.get('source_id')))}</td><td class='{_status_class(s.get('status'))}'>{escape(_v(s.get('status')))}</td><td>{escape(_v(s.get('source')))}</td><td>{escape(_v(s.get('last_update')))}</td><td>{escape(_v(s.get('refresh_interval_seconds')))}</td><td>{escape(_v(s.get('data_age_seconds')))}</td><td>{escape(_v(s.get('freshness')))}</td><td>{escape(_v(s.get('error_reason')))}</td><td>{escape(_v(s.get('retry_count')))}</td></tr>" for s in intelligence.get("sources",[]) if isinstance(s,dict)) or '<tr><td colspan="9">DATA_UNAVAILABLE</td></tr>'
    cross_rows=[]
    for s in cross.get("sources",[]) if isinstance(cross.get("sources"),list) else []:
        h=s.get("horizons",{}) if isinstance(s.get("horizons"),dict) else {}
        def hv(label,key): return _v((h.get(label) or {}).get(key)) if isinstance(h.get(label),dict) else DATA_UNAVAILABLE
        confidence=max([x for x in [hv(k,"confidence_percent") for k in ("24H","3D","5D","7D")] if isinstance(x,(int,float))],default=DATA_UNAVAILABLE)
        cross_rows.append(f"<tr><td>{escape(_v(s.get('source_id')))}</td><td>{escape(_v(s.get('category')))}</td><td class='{_status_class(s.get('status'))}'>{escape(_v(s.get('status')))}</td><td>{escape(_v(s.get('source')))}</td><td>{escape(_v(s.get('last_update')))}</td><td>{escape(_v(s.get('data_age_seconds')))}</td><td>{escape(_v(s.get('freshness')))}</td><td>{escape(_v(s.get('research_samples')))}</td><td>{escape(hv('24H','direction'))}</td><td>{escape(hv('3D','direction'))}</td><td>{escape(hv('5D','direction'))}</td><td>{escape(hv('7D','direction'))}</td><td>{escape(_v(confidence))}</td><td>{escape(_v(s.get('certification_status')))}</td></tr>")
    cross_html=''.join(cross_rows) or '<tr><td colspan="14">DATA_UNAVAILABLE · Run the real-source collector first.</td></tr>'
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="10"><title>AFIP Cross-Market Intelligence</title><style>body{{font-family:Arial,"Noto Sans Thai";margin:0;background:#eef2f6;color:#17202a}}.page{{padding:14px}}header,section{{background:white;border:1px solid #d8e0e8;border-radius:12px;padding:14px;margin-bottom:12px}}h1,h2{{margin:0 0 8px}}table{{width:100%;border-collapse:collapse;font-size:11px}}th,td{{border:1px solid #dde4eb;padding:6px;white-space:nowrap}}th{{background:#f3f6f9}}.ok{{background:#dff3e7;font-weight:bold}}.warn{{background:#fff1c9;font-weight:bold}}.bad{{background:#f8d7da;font-weight:bold}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}}.card{{border:1px solid #dde4eb;border-radius:9px;padding:10px}}a{{color:#245da8}}</style></head><body><div class="page"><header><a href="afip_dashboard.html">← Command Center</a><h1>🌐 Cross-Market Gold Intelligence</h1><p>Real-source only · Research first · No relationship is trading-eligible by assumption.</p></header><section><h2>Intelligence Health</h2><div class="cards"><div class="card"><b>Financial</b><br>{escape(_v(financial.get('portfolio_total',{}).get('status')))}</div><div class="card"><b>Verified Intelligence Sources</b><br>{escape(_v(intelligence.get('verified_sources')))} / {escape(_v(intelligence.get('source_count')))}</div><div class="card"><b>Cross-Market Health</b><br>{escape(_v(cross.get('overall_cross_market_health_percent')))}%</div><div class="card"><b>Pipeline Stage</b><br>{escape(_v(cross.get('pipeline_stage')))}</div></div></section><section><h2>AFIP Bank Live — Financial Integrity</h2><table><thead><tr><th>Profile</th><th>Status</th><th>Source</th><th>Balance</th><th>Equity</th><th>Allocation</th><th>Last Update</th><th>Age</th><th>Freshness</th><th>Retry</th><th>Connection</th></tr></thead><tbody>{financial_rows}</tbody></table></section><section><h2>Intelligence Runtime Certification</h2><table><thead><tr><th>Source ID</th><th>Status</th><th>Source</th><th>Last Update</th><th>Refresh</th><th>Age</th><th>Freshness</th><th>Error</th><th>Retries</th></tr></thead><tbody>{intel_rows}</tbody></table></section><section><h2>Cross-Market Research</h2><table><thead><tr><th>Market</th><th>Category</th><th>Status</th><th>Source</th><th>Last Update</th><th>Age</th><th>Freshness</th><th>Samples</th><th>24H</th><th>3D</th><th>5D</th><th>7D</th><th>Confidence</th><th>Certification</th></tr></thead><tbody>{cross_html}</tbody></table></section><section><h2>Research Coverage</h2><p>Collected samples: {escape(_v(cross.get('gold_samples')))} · Missing data remains DATA_UNAVAILABLE. Influence scores are recalculated from observed returns and remain RESEARCH_ONLY until evidence certification passes.</p><p>Gold mining AISC and non-MT5 macro/geopolitical sources are registered as external research sources; they are not marked connected without verified snapshots.</p></section></div></body></html>'''

def write_cross_market_dashboard(output_directory:str|Path="runtime/dashboard",project_root:str|Path=".")->Path:
    path=Path(output_directory)/FILENAME; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(render_cross_market_dashboard(project_root),encoding="utf-8"); return path
