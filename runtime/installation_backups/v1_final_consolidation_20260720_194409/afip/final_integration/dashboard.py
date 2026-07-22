from __future__ import annotations
from html import escape
import json
from pathlib import Path
from typing import Any
from .io import read_json
class UnifiedDashboardAuthority:
 def __init__(self,root:str|Path='.') -> None:self.root=Path(root).resolve()
 def build(self,output:str|Path='runtime/dashboard/afip_dashboard.html')->Path:
  from .runtime import FinalIntegrationRuntime
  central=FinalIntegrationRuntime(self.root).status().as_dict()
  sections=[('System',central),('Intelligence / Engine',read_json(self.root/'runtime/dashboard/dashboard_authority_snapshot.json')),('Research Engine',read_json(self.root/'runtime/research/research_engine_status.json')),('Profiles',central['trading_runtime']),('Operations',read_json(self.root/'runtime/research/research_live_status.json')),('Cross Market',read_json(self.root/'runtime/research/phase_v_major_status.json'))]
  nav=''.join(f'<a href="#s{i}">{escape(name)}</a>' for i,(name,_) in enumerate(sections))
  cards=''.join(f'<section id="s{i}"><h2>{escape(name)}</h2><pre>{escape(json.dumps(data,ensure_ascii=False,indent=2,default=str))}</pre></section>' for i,(name,data) in enumerate(sections))
  html=(f'<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="15"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AFIP V1 Dashboard</title><style>body{{margin:0;background:#09111f;color:#e8eef8;font-family:Segoe UI,Arial}}header{{position:sticky;top:0;background:#101a2d;padding:16px 22px;border-bottom:1px solid #263650}}nav{{display:flex;gap:8px;flex-wrap:wrap}}a{{color:#b9d5ff;text-decoration:none;background:#182743;padding:6px 10px;border-radius:8px}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:14px;padding:16px}}section{{background:#111d31;border:1px solid #263650;border-radius:12px;padding:14px;min-width:0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}</style></head><body><header><h1>AFIP Version 1.0 — Unified Dashboard</h1><nav>{nav}</nav></header><main>{cards}</main></body></html>')
  path=self.root/output;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(html,encoding='utf-8');return path
