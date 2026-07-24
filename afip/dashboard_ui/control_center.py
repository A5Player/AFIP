"""AFIP V1 passive Control Center dashboard."""
from __future__ import annotations
from html import escape
from pathlib import Path
from typing import Any, Mapping
from afip.control_center_runtime import ControlCenterRuntime

FILENAME = "afip_control_center.html"


def _text(value: Any, default: str = "DATA_UNAVAILABLE") -> str:
    text = str(value if value not in (None, "") else default)
    return escape(text)


def _rows(data: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    return "".join(f"<tr><th>{escape(key.replace('_',' ').title())}</th><td>{_text(data.get(key))}</td></tr>" for key in keys)


def render_control_center(project_root: str | Path = ".") -> str:
    snapshot = ControlCenterRuntime(project_root).snapshot()
    startup = snapshot.get("startup") if isinstance(snapshot.get("startup"), Mapping) else {}
    integration = snapshot.get("final_integration") if isinstance(snapshot.get("final_integration"), Mapping) else {}
    research = snapshot.get("research") if isinstance(snapshot.get("research"), Mapping) else {}
    dashboard = snapshot.get("dashboard") if isinstance(snapshot.get("dashboard"), Mapping) else {}
    profiles = snapshot.get("profiles") if isinstance(snapshot.get("profiles"), list) else []
    profile_cards = "".join(
        '<article><h3>{}</h3><table>{}</table></article>'.format(
            _text(p.get("profile_id"), "PROFILE"),
            _rows(p, ("runtime_state", "execution_mode", "armed", "connection_status", "mt5_connection", "decision", "confidence", "allocated_units", "sent_units", "waiting_reason", "reason", "login")),
        ) for p in profiles if isinstance(p, Mapping)
    )
    style = """
    :root{font-family:Arial,'Noto Sans Thai',sans-serif;color:#172033;background:#eef2f7}*{box-sizing:border-box}body{margin:0}.page{max-width:1500px;margin:auto;padding:18px}header,article{background:white;border:1px solid #d8e0ea;border-radius:12px;padding:16px;box-shadow:0 2px 8px #17203312}header{margin-bottom:14px}.nav{display:flex;flex-wrap:wrap;gap:8px}.nav a{padding:8px 10px;border-radius:8px;background:#16243b;color:white;text-decoration:none}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-bottom:14px}h1,h2,h3{margin-top:0}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:8px;border-bottom:1px solid #edf0f4;text-align:left;vertical-align:top}th{width:45%;color:#526277}.safe{color:#146c43;font-weight:700}.warning{color:#9b5b00;font-weight:700}.bar{height:12px;background:#e4e9ef;border-radius:999px;overflow:hidden}.bar span{display:block;height:100%;background:#2f7dd1}.muted{color:#64748b;font-size:12px}
    """
    progress = startup.get("progress_percent", 0) if isinstance(startup, Mapping) else 0
    try: progress_num = max(0.0, min(100.0, float(progress)))
    except (TypeError, ValueError): progress_num = 0.0
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><title>AFIP Control Center</title><style>{style}</style></head><body><div class="page"><header><div class="nav"><a href="afip_dashboard.html">Home</a><a href="afip_profiles_dashboard.html">Profiles</a><a href="afip_intelligence_engine_dashboard.html">Intelligence</a><a href="afip_research_data_dashboard.html">Research Data</a><a href="afip_research_operations_dashboard.html">Research Operations</a></div><h1>🎛️ AFIP V1 Control Center</h1><p>Passive production observability only · ไม่มีสิทธิ์ส่งคำสั่งซื้อขายหรือเปลี่ยน execution authority</p><div class="bar"><span style="width:{progress_num:.2f}%"></span></div><p><b>{progress_num:.2f}%</b> · {_text(startup.get('status'))} · {_text(startup.get('current_stage'))}</p></header><section class="grid"><article><h2>Startup</h2><table>{_rows(startup, ('status','current_stage','progress_percent','current_message','updated_at','warnings','errors'))}</table></article><article><h2>Operational Authority</h2><table>{_rows(integration, ('status','updated_at_utc'))}<tr><th>Execution authority changed</th><td class="safe">NO</td></tr><tr><th>Authority</th><td>Existing FinalIntegrationRuntime / Demo Execution Runtime</td></tr></table></article><article><h2>Research Runtime</h2><table>{_rows(research, ('status','current_operation','current_timeframe','symbol','available_bars','processed_bars','covered_bars','missing_bars','gap_count','progress_percent','queue_depth','last_error','updated_at'))}</table></article><article><h2>Dashboard Runtime</h2><table>{_rows(dashboard, ('status','last_generated_at','updated_at','process_state','pid'))}</table></article></section><h2>Profile Operations</h2><section class="grid">{profile_cards}</section><p class="muted">Generated {_text(snapshot.get('generated_at'))}. Missing producer data is shown as DATA_UNAVAILABLE; no values are invented.</p></div></body></html>'''


def write_control_center(output_directory: str | Path = "runtime/dashboard", project_root: str | Path = ".") -> Path:
    path = Path(output_directory) / FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(render_control_center(project_root), encoding="utf-8")
    temporary.replace(path)
    return path
