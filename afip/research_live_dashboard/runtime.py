from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")
DATA_UNAVAILABLE = "DATA_UNAVAILABLE"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _count_records(path: Path) -> int | None:
    try:
        if path.suffix.lower() == ".jsonl":
            return sum(1 for line in path.open("r", encoding="utf-8", errors="ignore") if line.strip())
        if path.suffix.lower() == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, list):
                return len(value)
            if isinstance(value, dict):
                for key in ("records", "candles", "bars", "rows", "data", "observations", "samples"):
                    item = value.get(key)
                    if isinstance(item, list):
                        return len(item)
    except Exception:
        return None
    return None


def build_live_snapshot(root: str | Path = ".", stage: str = "OBSERVING", reason: str = "runtime_snapshot") -> dict[str, Any]:
    project = Path(root)
    lake = project / "runtime/research/historical_data_lake"
    coverage: dict[str, dict[str, Any]] = {}
    all_files = [p for p in lake.rglob("*") if p.is_file()] if lake.exists() else []
    for timeframe in TIMEFRAMES:
        token = timeframe.lower()
        matched = [p for p in all_files if token in str(p).lower().replace("timeframe=", "")]
        records = 0
        known_record_files = 0
        total_bytes = 0
        newest: float | None = None
        for path in matched:
            try:
                stat = path.stat(); total_bytes += stat.st_size
                newest = stat.st_mtime if newest is None else max(newest, stat.st_mtime)
            except OSError:
                pass
            count = _count_records(path)
            if count is not None:
                records += count; known_record_files += 1
        coverage[timeframe] = {
            "status": "AVAILABLE" if matched else "DATA_UNAVAILABLE",
            "file_count": len(matched),
            "record_count": records if known_record_files else DATA_UNAVAILABLE,
            "bytes": total_bytes,
            "last_write_utc": datetime.fromtimestamp(newest, timezone.utc).isoformat().replace("+00:00", "Z") if newest else DATA_UNAVAILABLE,
        }

    latest_path = project / "runtime/research/cross_market/latest.json"
    evidence_path = project / "runtime/research/cross_market/evidence.json"
    collector_path = project / "runtime/research/cross_market/collector_status.json"
    latest, evidence, collector = _load(latest_path), _load(evidence_path), _load(collector_path)
    snapshot = {
        "schema_version": "phase_u_research_live_observability_v1",
        "generated_at": _utc(),
        "status": "RUNNING",
        "stage": stage,
        "reason": reason,
        "execution_authority": False,
        "live_execution_enabled": False,
        "order_send_called": False,
        "timeframe_coverage": coverage,
        "historical_data_lake": {"file_count": len(all_files), "root": str(lake)},
        "cross_market": {
            "pipeline_stage": latest.get("pipeline_stage", DATA_UNAVAILABLE),
            "gold_samples": latest.get("gold_samples", DATA_UNAVAILABLE),
            "source_count": len(latest.get("sources", [])) if isinstance(latest.get("sources"), list) else DATA_UNAVAILABLE,
            "observation_count": evidence.get("observation_count", DATA_UNAVAILABLE),
            "last_cycle": collector.get("last_cycle", DATA_UNAVAILABLE),
        },
    }
    out = project / "runtime/research/research_live_status.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return snapshot


def render_live_dashboard(snapshot: dict[str, Any]) -> str:
    rows = []
    for tf in TIMEFRAMES:
        item = snapshot.get("timeframe_coverage", {}).get(tf, {})
        status = str(item.get("status", DATA_UNAVAILABLE))
        css = "ok" if status == "AVAILABLE" else "warn"
        rows.append(
            "<tr>" +
            f"<td><b>{tf}</b></td><td class='{css}'>{html.escape(status)}</td>" +
            f"<td>{html.escape(str(item.get('file_count', 0)))}</td>" +
            f"<td>{html.escape(str(item.get('record_count', DATA_UNAVAILABLE)))}</td>" +
            f"<td>{html.escape(str(item.get('bytes', 0)))}</td>" +
            f"<td>{html.escape(str(item.get('last_write_utc', DATA_UNAVAILABLE)))}</td></tr>"
        )
    cross = snapshot.get("cross_market", {})
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="10"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AFIP Research Live</title><style>
body{{font-family:Arial,"Noto Sans Thai";margin:0;background:#eef2f6;color:#17202a}}.page{{padding:14px}}header,section{{background:#fff;border:1px solid #d8e0e8;border-radius:12px;padding:14px;margin-bottom:12px}}.pulse{{display:inline-block;width:11px;height:11px;border-radius:50%;background:#24a148;animation:p 1.2s infinite}}@keyframes p{{50%{{opacity:.25}}}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}}.card{{border:1px solid #dde4eb;border-radius:9px;padding:10px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #dde4eb;padding:7px;text-align:left}}th{{background:#f3f6f9}}.ok{{background:#dff3e7;font-weight:bold}}.warn{{background:#fff1c9;font-weight:bold}}.safe{{padding:10px;background:#e8f4ff;border-radius:8px}}</style></head><body><div class="page">
<header><a href="afip_dashboard.html">← Command Center</a><h1><span class="pulse"></span> AFIP Research Live Dashboard</h1><p>อัปเดตหน้าอัตโนมัติทุก 10 วินาที · แสดงเฉพาะหลักฐานที่พบจริง · ไม่สร้างข้อมูลสมมุติ</p><div class="safe">Research only · execution_authority=false · order_send_called=false</div></header>
<section><div class="cards"><div class="card"><b>Status</b><br>{html.escape(str(snapshot.get('status')))}</div><div class="card"><b>Stage</b><br>{html.escape(str(snapshot.get('stage')))}</div><div class="card"><b>Reason</b><br>{html.escape(str(snapshot.get('reason')))}</div><div class="card"><b>Last Snapshot UTC</b><br>{html.escape(str(snapshot.get('generated_at')))}</div><div class="card"><b>Lake Files</b><br>{html.escape(str(snapshot.get('historical_data_lake',{}).get('file_count')))}</div><div class="card"><b>Last Research Cycle</b><br>{html.escape(str(cross.get('last_cycle',DATA_UNAVAILABLE)))}</div></div></section>
<section><h2>Timeframe Data Coverage — M1 to D1</h2><table><thead><tr><th>Timeframe</th><th>Status</th><th>Files</th><th>Records</th><th>Bytes</th><th>Last Write UTC</th></tr></thead><tbody>{''.join(rows)}</tbody></table><p>DATA_UNAVAILABLE หมายถึงยังไม่พบหลักฐานใน Data Lake ไม่ได้แปลว่าระบบโหลดสำเร็จแล้ว</p></section>
<section><h2>Research / Replay Evidence</h2><div class="cards"><div class="card"><b>Pipeline Stage</b><br>{html.escape(str(cross.get('pipeline_stage',DATA_UNAVAILABLE)))}</div><div class="card"><b>Gold Samples</b><br>{html.escape(str(cross.get('gold_samples',DATA_UNAVAILABLE)))}</div><div class="card"><b>Cross-market Sources</b><br>{html.escape(str(cross.get('source_count',DATA_UNAVAILABLE)))}</div><div class="card"><b>Evidence Observations</b><br>{html.escape(str(cross.get('observation_count',DATA_UNAVAILABLE)))}</div></div></section>
</div></body></html>'''


def write_live_dashboard(root: str | Path = ".", snapshot: dict[str, Any] | None = None) -> Path:
    project = Path(root)
    current = snapshot or build_live_snapshot(project)
    out = project / "runtime/dashboard/afip_research_live_dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_live_dashboard(current), encoding="utf-8")
    return out
