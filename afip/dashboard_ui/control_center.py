"""AFIP Pro passive Control Center dashboard."""

from __future__ import annotations

from afip.branding import CONTROL_CENTER_NAME
from html import escape
from pathlib import Path
from typing import Any, Mapping
import json
from afip.control_center_runtime import ControlCenterRuntime

FILENAME = "afip_control_center.html"
PROFILE_DETAIL_FILENAMES = {profile_id: f"afip_{profile_id.lower()}_detail.html" for profile_id in ("P1", "P2", "P3", "P4")}


def _text(value: Any, default: str = "DATA_UNAVAILABLE") -> str:
    text = str(value if value not in (None, "") else default)
    return escape(text)


def _rows(data: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    return "".join(f"<tr><th>{escape(key.replace('_',' ').title())}</th><td>{_text(data.get(key))}</td></tr>" for key in keys)



def _timeline_rows(stages: Any) -> str:
    if not isinstance(stages, list) or not stages:
        return '<tr><td colspan="4">NOT_RECORDED</td></tr>'
    rows = []
    for row in stages:
        if not isinstance(row, Mapping):
            continue
        rows.append('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
            _text(row.get("stage")), _text(row.get("status")), _text(row.get("value")), _text(row.get("reason"))
        ))
    return ''.join(rows) or '<tr><td colspan="4">NOT_RECORDED</td></tr>'


def _observatory_rows(rows: Any) -> str:
    if not isinstance(rows, list) or not rows:
        return '<tr><td colspan="3">NOT_RECORDED</td></tr>'
    return ''.join('<tr><td>{}</td><td>{}</td><td>{}</td></tr>'.format(_text(r.get("component")), _text(r.get("status")), _text(r.get("reason"))) for r in rows if isinstance(r, Mapping))


def render_control_center(project_root: str | Path = ".") -> str:
    snapshot = ControlCenterRuntime(project_root).snapshot()
    startup = snapshot.get("startup") if isinstance(snapshot.get("startup"), Mapping) else {}
    integration = snapshot.get("final_integration") if isinstance(snapshot.get("final_integration"), Mapping) else {}
    authority = snapshot.get("runtime_authority") if isinstance(snapshot.get("runtime_authority"), Mapping) else {}
    research = snapshot.get("research") if isinstance(snapshot.get("research"), Mapping) else {}
    trading_modes = snapshot.get("profile_trading_modes") if isinstance(snapshot.get("profile_trading_modes"), Mapping) else {}
    truth = snapshot.get("runtime_truth") if isinstance(snapshot.get("runtime_truth"), Mapping) else {}
    dashboard = snapshot.get("dashboard") if isinstance(snapshot.get("dashboard"), Mapping) else {}
    explainability = snapshot.get("explainability") if isinstance(snapshot.get("explainability"), Mapping) else {}
    observatory = snapshot.get("runtime_observatory") if isinstance(snapshot.get("runtime_observatory"), Mapping) else {}
    profiles = snapshot.get("profiles") if isinstance(snapshot.get("profiles"), list) else []
    profile_cards = "".join(
        '<article><h3>{} · <a href="{}">รายละเอียดทั้งหมด</a></h3><table>{}</table></article>'.format(
            _text(p.get("profile_id"), "PROFILE"),
            PROFILE_DETAIL_FILENAMES.get(str(p.get("profile_id", "")).upper(), "afip_control_center.html"),
            _rows(p, ("trading_mode", "trading_mode_allowed", "trading_mode_reason", "runtime_state", "execution_mode", "armed", "connection_status", "mt5_connection", "decision", "confidence", "entry_mode", "trade_case_id", "initial_units", "reserved_units", "capacity_is_ceiling_not_target", "intelligence_modules", "decision_scenario", "decision_conflict_reason", "account_balance", "account_equity", "available_capital", "capital_basis", "capital_units", "confidence_units", "risk_units", "profile_max_units", "execution_safety_units", "lot_limiting_gate", "approved_lot_per_order", "total_approved_lot", "lot_authority_policy", "allocated_units", "sent_units", "execution_batch_id", "execution_outcome", "execution_attempts", "execution_latency_ms", "partial_execution", "remaining_units", "reconciliation_required", "retry_policy", "positions_evaluated", "position_care_action", "position_care_reason", "care_intelligence_scenario", "care_intelligence_confidence", "position_action_status", "position_action_reason", "break_even_policy", "trailing_policy", "partial_close_policy", "pyramiding_policy", "waiting_reason", "reason", "login")),
        ) for p in profiles if isinstance(p, Mapping)
    )
    explain_cards = "".join(
        '<article class="wide"><h3>{}</h3><p><b>Trace:</b> {} · <b>Decision:</b> {} · <b>Confidence:</b> {} · <b>First blocker:</b> {}</p><table><thead><tr><th>Stage</th><th>Status</th><th>Value</th><th>Reason</th></tr></thead><tbody>{}</tbody></table><h4>Position Care</h4><table>{}</table></article>'.format(
            _text(p.get("profile_id"), "PROFILE"),
            _text((p.get("decision_explainability") or {}).get("trace_id")) if isinstance(p.get("decision_explainability"), Mapping) else "NOT_RECORDED",
            _text((p.get("decision_explainability") or {}).get("decision")) if isinstance(p.get("decision_explainability"), Mapping) else "NOT_RECORDED",
            _text((p.get("decision_explainability") or {}).get("confidence")) if isinstance(p.get("decision_explainability"), Mapping) else "NOT_RECORDED",
            _text((p.get("decision_explainability") or {}).get("first_blocking_stage")) if isinstance(p.get("decision_explainability"), Mapping) else "NOT_RECORDED",
            _timeline_rows((p.get("decision_explainability") or {}).get("stages")) if isinstance(p.get("decision_explainability"), Mapping) else _timeline_rows([]),
            _rows(p.get("position_explainability") if isinstance(p.get("position_explainability"), Mapping) else {}, ("status","ticket","recommended_action","reason_codes","proposed_stop_price","mt5_action_status","mt5_action_reason","intelligence_scenario","intelligence_confidence","execution_trace_id","source")),
        ) for p in profiles if isinstance(p, Mapping)
    )
    style = """
    :root{font-family:Arial,'Noto Sans Thai',sans-serif;color:#172033;background:#eef2f7}*{box-sizing:border-box}body{margin:0}.page{max-width:1500px;margin:auto;padding:18px}header,article{background:white;border:1px solid #d8e0ea;border-radius:12px;padding:16px;box-shadow:0 2px 8px #17203312}header{margin-bottom:14px}.nav{display:flex;flex-wrap:wrap;gap:8px}.nav a{padding:8px 10px;border-radius:8px;background:#16243b;color:white;text-decoration:none}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:14px}.grid article{min-width:0;overflow:hidden}.grid table{table-layout:fixed;font-size:11px}.grid th,.grid td{padding:6px;overflow-wrap:anywhere}.grid th{width:44%}.explain-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.wide table th{width:auto}.wide thead th{background:#f5f7fa}.wide h4{margin-bottom:6px}@media(max-width:1200px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:700px){.grid{grid-template-columns:1fr}}h1,h2,h3{margin-top:0}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:8px;border-bottom:1px solid #edf0f4;text-align:left;vertical-align:top}th{width:45%;color:#526277}.safe{color:#146c43;font-weight:700}.warning{color:#9b5b00;font-weight:700}.bar{height:12px;background:#e4e9ef;border-radius:999px;overflow:hidden}.bar span{display:block;height:100%;background:#2f7dd1}.muted{color:#64748b;font-size:12px}
    """
    progress = startup.get("progress_percent", 0) if isinstance(startup, Mapping) else 0
    try: progress_num = max(0.0, min(100.0, float(progress)))
    except (TypeError, ValueError): progress_num = 0.0
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><title>{CONTROL_CENTER_NAME}</title><style>{style}</style></head><body><div class="page"><header><div class="nav"><a href="afip_dashboard.html">Home</a><a href="afip_profiles_dashboard.html">Profiles</a><a href="afip_p1_detail.html">P1</a><a href="afip_p2_detail.html">P2</a><a href="afip_p3_detail.html">P3</a><a href="afip_p4_detail.html">P4</a><a href="afip_intelligence_engine_dashboard.html">Intelligence</a><a href="afip_research_data_dashboard.html">Research Data</a><a href="afip_research_operations_dashboard.html">Research Operations</a></div><h1>🎛️ {CONTROL_CENTER_NAME}</h1><p>Passive production observability only · ไม่มีสิทธิ์ส่งคำสั่งซื้อขายหรือเปลี่ยน execution authority</p><div class="bar"><span style="width:{progress_num:.2f}%"></span></div><p><b>{progress_num:.2f}%</b> · {_text(startup.get('status'))} · {_text(startup.get('current_stage'))}</p></header><section class="grid"><article><h2>Profile Trading Modes</h2><table>{_rows(trading_modes, ('status','profiles','account_activation_policy','execution_authority_changed'))}</table></article><article><h2>Startup</h2><table>{_rows(startup, ('status','current_stage','progress_percent','current_message','updated_at','warnings','errors'))}</table></article><article><h2>Runtime Authority</h2><table>{_rows(authority, ('status','canonical_lifecycle_authority','desired_state','desired_state_reason','router_state','router_pid','watchdog_state','watchdog_pid','duplicate_process_risk'))}<tr><th>MT5 Auto Launch Allowed</th><td>{_text(authority.get('mt5_auto_launch_allowed'))}</td></tr><tr><th>Execution authority changed</th><td class="safe">{_text(authority.get('execution_authority_changed'))}</td></tr></table></article><article><h2>Runtime Truth</h2><table>{_rows(truth, ('status','policy','domains_certified','domains_total','conflict_count','missing_authority_count'))}<tr><th>Execution authority changed</th><td class="safe">{_text(truth.get('execution_authority_changed'))}</td></tr></table></article><article><h2>Research Runtime</h2><table>{_rows(research, ('status','research_bridge_status','trade_cases_written','holding_observations','exits_recorded','single_unit_profit_pattern_observations','initial_capital_pattern_observations','research_standards_updated','current_operation','current_timeframe','symbol','available_bars','processed_bars','covered_bars','missing_bars','gap_count','progress_percent','queue_depth','last_error','updated_at'))}</table></article><article><h2>Dashboard Runtime</h2><table>{_rows(dashboard, ('status','last_generated_at','updated_at','process_state','pid'))}</table></article><article><h2>Runtime Observatory</h2><p><b>{_text(observatory.get('status'))}</b> · critical {_text(observatory.get('critical_count'))} · degraded {_text(observatory.get('degraded_count'))}</p><table><thead><tr><th>Component</th><th>Status</th><th>Reason</th></tr></thead><tbody>{_observatory_rows(observatory.get('components'))}</tbody></table></article></section><h2>Explainable Decision Timeline</h2><p class="muted">Policy: {_text(explainability.get('policy'))}. Explanations are projected only from recorded runtime artifacts.</p><section class="explain-grid">{explain_cards}</section><h2>Profile Operations</h2><section class="grid">{profile_cards}</section><p class="muted">Generated {_text(snapshot.get('generated_at'))}. Missing producer data is shown as DATA_UNAVAILABLE; no values are invented.</p></div></body></html>'''


def render_profile_detail(project_root: str | Path, profile_id: str) -> str:
    """Render one profile without creating another runtime or data authority."""
    pid = profile_id.strip().upper()
    if pid not in PROFILE_DETAIL_FILENAMES:
        raise ValueError("profile_id_must_be_p1_to_p4")
    snapshot = ControlCenterRuntime(project_root).snapshot()
    profile = next((row for row in snapshot.get("profiles", []) if isinstance(row, Mapping) and row.get("profile_id") == pid), {})
    research = snapshot.get("research") if isinstance(snapshot.get("research"), Mapping) else {}
    trading_modes = snapshot.get("profile_trading_modes") if isinstance(snapshot.get("profile_trading_modes"), Mapping) else {}
    decision = profile.get("decision_explainability") if isinstance(profile.get("decision_explainability"), Mapping) else {}
    position = profile.get("position_explainability") if isinstance(profile.get("position_explainability"), Mapping) else {}
    all_keys = tuple(sorted(key for key in profile if key not in {"decision_explainability", "position_explainability"}))
    raw = escape(json.dumps(profile, indent=2, ensure_ascii=False, default=str))
    style = "body{font-family:Arial,'Noto Sans Thai',sans-serif;background:#eef2f7;color:#172033;margin:0}.page{max-width:1200px;margin:auto;padding:18px}article,header{background:#fff;border:1px solid #d8e0ea;border-radius:12px;padding:16px;margin-bottom:14px}a{color:#1769aa}table{width:100%;border-collapse:collapse}th,td{padding:8px;border-bottom:1px solid #edf0f4;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{width:34%;color:#526277}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#111827;color:#e5edf8;padding:12px;border-radius:8px}.nav{display:flex;gap:10px;flex-wrap:wrap}"
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="5"><title>AFIP {pid} Detail</title><style>{style}</style></head><body><div class="page"><header><div class="nav"><a href="afip_dashboard.html">Home</a><a href="afip_control_center.html">P1–P4 รวม</a>{''.join(f'<a href="{filename}">{name}</a>' for name,filename in PROFILE_DETAIL_FILENAMES.items())}</div><h1>{pid} — รายละเอียดการคิดและการรอ</h1><p>อ่านจากหลักฐาน Runtime เท่านั้น ไม่มีสิทธิ์สั่งเทรดหรือเปลี่ยนโหมด</p></header><article><h2>Trading Mode</h2><table>{_rows(trading_modes, ('status','profiles','account_activation_policy','execution_authority_changed'))}</table></article><article><h2>สถานะ {pid} ทั้งหมด</h2><table>{_rows(profile, all_keys)}</table></article><article><h2>เหตุผลการตัดสินใจ</h2><table>{_rows(decision, ('trace_id','decision','confidence','first_blocking_stage','first_blocking_reason','waiting_for'))}</table><table><thead><tr><th>Stage</th><th>Status</th><th>Value</th><th>Reason</th></tr></thead><tbody>{_timeline_rows(decision.get('stages'))}</tbody></table></article><article><h2>การดูแลออเดอร์และกำไร</h2><table>{_rows(position, tuple(sorted(position.keys())))}</table></article><article><h2>งานวิจัยที่เกี่ยวข้อง</h2><table>{_rows(research, ('status','current_operation','current_timeframe','single_unit_profit_pattern_observations','initial_capital_pattern_observations','research_standards_updated','progress_percent','last_error','updated_at'))}</table></article><article><h2>หลักฐานดิบของ {pid}</h2><pre>{raw}</pre></article></div></body></html>'''


def write_control_center(output_directory: str | Path = "runtime/dashboard", project_root: str | Path = ".") -> Path:
    path = Path(output_directory) / FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(render_control_center(project_root), encoding="utf-8")
    temporary.replace(path)
    return path
