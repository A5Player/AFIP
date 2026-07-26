from __future__ import annotations

from pathlib import Path
from typing import Iterable

_PRIMARY_DASHBOARDS = (
    "afip_profiles_dashboard.html",
    "afip_intelligence_engine_dashboard.html",
    "afip_order_evidence_dashboard.html",
    "afip_live_mt5_dashboard.html",
    "afip_research_data_dashboard.html",
)

_STYLE_MARKER = 'id="afip-bottom-safety-space"'
_STYLE_BLOCK = (
    '<style id="afip-bottom-safety-space">'
    'html,body{min-height:100%;}'
    'body{padding-bottom:100px!important;box-sizing:border-box;}'
    '</style>'
)


def _inject_bottom_safety_space(text: str) -> tuple[str, bool]:
    if (
        _STYLE_MARKER in text
        or "padding-bottom:100px" in text
        or "padding-bottom: 100px" in text
        or "padding-bottom:110px" in text
        or "padding-bottom: 110px" in text
        or "padding-bottom:96px" in text
    ):
        return text, False

    lower = text.lower()
    head_end = lower.find("</head>")
    if head_end >= 0:
        return text[:head_end] + _STYLE_BLOCK + text[head_end:], True

    body_end = lower.find("</body>")
    if body_end >= 0:
        return text[:body_end] + _STYLE_BLOCK + text[body_end:], True

    return text + _STYLE_BLOCK, True


def ensure_primary_dashboard_bottom_safety(
    dashboard_root: str | Path = "runtime/dashboard",
    names: Iterable[str] = _PRIMARY_DASHBOARDS,
) -> dict[str, object]:
    root = Path(dashboard_root)
    updated: list[str] = []
    missing: list[str] = []
    unchanged: list[str] = []

    for name in names:
        path = root / name
        if not path.exists():
            missing.append(name)
            continue

        original = path.read_text(encoding="utf-8")
        repaired, changed = _inject_bottom_safety_space(original)
        if changed:
            path.write_text(repaired, encoding="utf-8")
            updated.append(name)
        else:
            unchanged.append(name)

    return {
        "status": "PASS",
        "dashboard_root": str(root),
        "updated": updated,
        "unchanged": unchanged,
        "missing": missing,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(ensure_primary_dashboard_bottom_safety(), indent=2))
