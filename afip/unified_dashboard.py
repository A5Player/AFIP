"""Iframe-free unified AFIP dashboard for reliable local-file display."""
from __future__ import annotations
from html import escape
from pathlib import Path
from typing import Any, Mapping
FILENAME='afip_unified_dashboard.html'

def render(contract:Mapping[str,Any])->str:
    profiles=[]
    for p in contract.get('profiles',[]):
        pid=escape(str(p.get('profile_id','UNKNOWN')))
        truth=p.get('authoritative_runtime_truth') if isinstance(p.get('authoritative_runtime_truth'),Mapping) else {}
        status=escape(str(truth.get('operational_state','DATA_UNAVAILABLE')))
        reason=escape(str(truth.get('reason','no_runtime_reason_recorded')))
        profiles.append(f'<article><h2>{pid}</h2><div class="status">{status}</div><p>{reason}</p><dl><dt>AFIP Runtime</dt><dd>{escape(str(truth.get("runtime_state","DATA_UNAVAILABLE")))}</dd><dt>MT5 Process</dt><dd>{escape(str(truth.get("process_state","DATA_UNAVAILABLE")))}</dd><dt>Connection</dt><dd>{escape(str(truth.get("session_state","DATA_UNAVAILABLE")))}</dd><dt>Decision</dt><dd>{escape(str(p.get("decision","NOT_GENERATED")))}</dd><dt>Confidence</dt><dd>{escape(str(p.get("confidence","NOT_GENERATED")))}</dd><dt>Order</dt><dd>{escape(str(p.get("order_status","NO_ORDER_SENT")))}</dd><dt>Data</dt><dd>{escape(str(p.get("data_status","DATA_UNAVAILABLE")))}</dd></dl></article>')
    links=[('Execution Pipeline','afip_execution_pipeline_dashboard.html'),('Order Evidence','afip_order_evidence_dashboard.html'),('Live MT5','afip_live_mt5_dashboard.html'),('Research','afip_research_observability_dashboard.html'),('Audit','afip_dashboard_audit.html'),('Legacy Command Center','afip_dashboard.html')]
    nav=''.join(f'<a href="{u}">{escape(t)}</a>' for t,u in links)
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="5"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AFIP Unified Dashboard</title><style>body{{font-family:Arial,sans-serif;background:#eef2f7;margin:0;color:#172033}}header{{background:#101a2b;color:white;padding:18px 22px}}nav{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}nav a{{color:white;text-decoration:none;background:#263a58;padding:8px 10px;border-radius:8px;font-size:12px}}main{{padding:20px;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}article{{background:white;border:1px solid #d6deea;border-radius:12px;padding:16px}}.status{{font-weight:800;color:#245f9e}}dl{{display:grid;grid-template-columns:110px 1fr;gap:8px;font-size:13px}}dt{{color:#68798f}}dd{{margin:0;word-break:break-word}}.banner{{grid-column:1/-1;background:#fff6d8;border-radius:10px;padding:12px}}</style></head><body><header><h1>AFIP Unified Runtime Dashboard</h1><p>Iframe-free local display · refresh every 5 seconds · contract status: {escape(str(contract.get('status','UNKNOWN')))}</p><nav>{nav}</nav></header><main><div class="banner">This page embeds runtime evidence directly, so it remains visible when browser file:// iframe restrictions block the legacy command center.</div>{''.join(profiles) or '<article>No profile evidence available.</article>'}</main></body></html>'''

def write(contract:Mapping[str,Any],output_directory:str|Path='runtime/dashboard')->Path:
    p=Path(output_directory)/FILENAME;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render(contract),encoding='utf-8');return p
