"""Read-only research observability dashboard."""
from __future__ import annotations
from html import escape
from pathlib import Path
from typing import Any, Mapping
FILENAME='afip_research_observability_dashboard.html'

def _flatten(m:Mapping[str,Any],prefix=''):
    out=[]
    for k,v in m.items():
        name=f'{prefix}.{k}' if prefix else str(k)
        if isinstance(v,Mapping): out.extend(_flatten(v,name))
        elif isinstance(v,(str,int,float,bool)) or v is None: out.append((name,v))
    return out

def render(contract:Mapping[str,Any])->str:
    research=contract.get('research') if isinstance(contract.get('research'),Mapping) else {}
    research_rows=_flatten(research)[:80]
    research_body=''.join(f'<tr><th>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>' for k,v in research_rows)
    audit_rows=[]
    for name,meta in (contract.get('sources') or {}).items():
        if not isinstance(meta,Mapping):
            continue
        audit_rows.append(
            '<tr><td>'+escape(str(name))+'</td><td>'+escape(str(meta.get('exists')))+'</td>'
            '<td>'+escape(str(meta.get('readable')))+'</td><td>'+escape(str(meta.get('age_seconds')))+'</td>'
            '<td>'+escape(str(meta.get('fresh')))+'</td></tr>'
        )
    audit_body=''.join(audit_rows)
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AFIP Observability & Audit</title><style>
*{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;background:#eef2f7;margin:0;padding:14px 14px 100px;color:#172033}}h1{{margin:0 0 4px;font-size:22px}}p{{margin:0 0 12px;color:#607089;font-size:12px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;height:calc(100vh - 155px);min-height:520px}}section{{background:white;border:1px solid #d6deea;border-radius:12px;padding:12px;overflow:hidden;display:flex;flex-direction:column}}h2{{font-size:15px;margin:0 0 8px}}.table-wrap{{overflow:auto;min-height:0;flex:1}}table{{width:100%;border-collapse:collapse}}th,td{{padding:6px;border-bottom:1px solid #edf1f6;text-align:left;font-size:10px}}th{{color:#607089;width:45%}}.audit th{{width:auto;background:#f7f9fc;position:sticky;top:0}}@media(max-width:900px){{.grid{{grid-template-columns:1fr;height:auto}}section{{max-height:560px}}}}
</style></head><body><h1>Research Observability & Dashboard Audit</h1><p>Low-priority diagnostic evidence combined on one page. Read-only.</p><main class="grid"><section><h2>Research Observability</h2><div class="table-wrap"><table>{research_body or '<tr><td>DATA_UNAVAILABLE</td></tr>'}</table></div></section><section><h2>Dashboard Source Audit</h2><div class="table-wrap"><table class="audit"><thead><tr><th>Source</th><th>Exists</th><th>Readable</th><th>Age</th><th>Fresh</th></tr></thead><tbody>{audit_body}</tbody></table></div></section></main></body></html>'''

def write(contract:Mapping[str,Any],output_directory:str|Path='runtime/dashboard')->Path:
    p=Path(output_directory)/FILENAME;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render(contract),encoding='utf-8');return p
