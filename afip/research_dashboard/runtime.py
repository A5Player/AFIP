"""Static, dependency-free research dashboard renderer."""

from __future__ import annotations
import html
from typing import Any, Mapping

def _table(rows, columns):
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key, _ in columns)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

def build_research_dashboard(report: Mapping[str, Any]) -> str:
    top = list(report.get("top_overall", []))
    low_dd = list(report.get("top_low_drawdown", []))
    bottom = list(report.get("bottom_and_quarantined", []))
    columns = [
        ("research_id", "Research ID"),
        ("ranking_score", "Score"),
        ("win_rate_percentage", "Win Rate %"),
        ("maximum_drawdown_percentage", "Maximum Drawdown %"),
        ("expectancy", "Expectancy"),
        ("profit_factor", "Profit Factor"),
        ("evidence_status", "Status"),
    ]
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>AFIP Research Dashboard</title>
<style>
body{{font-family:Arial,sans-serif;margin:24px;line-height:1.4}}
section{{margin:28px 0}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #bbb;padding:7px;text-align:left}} th{{font-weight:700}}
.notice{{padding:12px;border:1px solid #999}}
</style></head><body>
<h1>AFIP Research Dashboard</h1>
<div class="notice">Research evidence is advisory. Execution permission remains outside this dashboard.</div>
<section><h2>Top Overall</h2>{_table(top, columns)}</section>
<section><h2>Top Low Drawdown</h2>{_table(low_dd, columns)}</section>
<section><h2>Bottom and Quarantined</h2>{_table(bottom, columns)}</section>
</body></html>"""
