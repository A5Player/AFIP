from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOKENS = {
    "forced_three": [
        r"allocated_units\s*=\s*3\b",
        r"range\(\s*3\s*\)",
        r"maximum_units[\"']?\s*[,)]",
    ],
    "legacy_tp_500": [
        r"take_profit_points\s*=\s*500\b",
        r"tp_points\s*=\s*500\b",
        r"\b500(?:\.0)?\b",
    ],
    "legacy_sl_3000": [
        r"stop_loss_points\s*=\s*3000\b",
        r"sl_points\s*=\s*3000\b",
        r"\b3000(?:\.0)?\b",
    ],
    "order_send": [
        r"\border_send\s*\(",
        r"mt5\.order_send\s*\(",
    ],
}

EXCLUDE_PARTS = {".git", ".venv", "runtime", "__pycache__", "tests"}

findings = []
for path in ROOT.rglob("*.py"):
    if any(part in EXCLUDE_PARTS for part in path.parts):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for category, patterns in TOKENS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                line = text.count("\n", 0, match.start()) + 1
                findings.append({
                    "category": category,
                    "path": str(path.relative_to(ROOT)),
                    "line": line,
                    "match": match.group(0),
                })

report = {
    "status": "REVIEW_REQUIRED" if findings else "NO_MATCHES",
    "root": str(ROOT),
    "findings": findings,
    "instruction": (
        "Inspect the exact execution gateway call path. Wire approve_execution() "
        "immediately before MT5 order_check/order_send. Never replace maximum_units "
        "with forced allocation. Reject missing protection plans."
    ),
}

output = ROOT / "runtime" / "audit" / "milestone_s_pack_4_9_source_audit.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
print(f"Report: {output}")
