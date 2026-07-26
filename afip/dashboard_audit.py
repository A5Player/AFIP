"""Dashboard source audit page."""
from __future__ import annotations
from html import escape
from pathlib import Path
from typing import Any, Mapping
FILENAME='afip_dashboard_audit.html'

def render(contract:Mapping[str,Any])->str:
    rows=[]
    for name,meta in (contract.get('sources') or {}).items():
        if not isinstance(meta,Mapping): continue
        rows.append(f"<tr><td>{escape(str(name))}</td><td>{escape(str(meta.get('path','')))}</td><td>{escape(str(meta.get('current_state','UNKNOWN')))}</td><td>{escape(str(meta.get('exists')))}</td><td>{escape(str(meta.get('readable')))}</td><td>{escape(str(meta.get('age_seconds')))}</td><td>{escape(str(meta.get('producer','NOT_RECORDED')))}</td><td>{escape(str(meta.get('pid','NOT_RECORDED')))}</td><td>{escape(str(meta.get('execution_mode','NOT_RECORDED')))}</td></tr>")
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AFIP Dashboard Audit</title><style>body{{font-family:Arial,sans-serif;background:#eef2f7;margin:0;padding:20px;color:#172033}}table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden}}th,td{{padding:10px;border-bottom:1px solid #e8edf4;text-align:left;font-size:13px}}</style></head><body><h1>Dashboard Audit Mode</h1><p>Every dashboard source, current/stale state, provenance, process and execution mode.</p><table><thead><tr><th>Source</th><th>Path</th><th>State</th><th>Exists</th><th>Readable</th><th>Age (s)</th><th>Producer</th><th>PID</th><th>Execution Mode</th></tr></thead><tbody>{''.join(rows)}</tbody></table></body></html>'''

def write(contract:Mapping[str,Any],output_directory:str|Path='runtime/dashboard')->Path:
    p=Path(output_directory)/FILENAME;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render(contract),encoding='utf-8');return p
