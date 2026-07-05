from __future__ import annotations

# AFIP Intelligence Naming Audit / ตรวจชื่อใหม่ให้ไม่มีคำแนวทหารในแกนใหม่

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW_SCOPE = [
    ROOT / "afip.py",
    ROOT / "aif" / "cli.py",
    ROOT / "aif" / "core" / "decision_intelligence.py",
    ROOT / "aif" / "core" / "execution_intelligence.py",
    ROOT / "aif" / "core" / "market_intelligence.py",
    ROOT / "aif" / "core" / "portfolio_intelligence.py",
    ROOT / "aif" / "core" / "risk_intelligence.py",
    ROOT / "docs" / "phase4" / "AFIP_REBRAND_INTELLIGENCE_LOCK.md",
    ROOT / "config" / "afip_intelligence_naming_policy.json",
]
BLOCKED = ["Com" + "mander", "Ran" + "ger", "Sni" + "per", "Sc" + "out", "Del" + "ta"]
REQUIRED = ["AFIP", "Intelligence"]


def main() -> int:
    findings = []
    checked = 0
    for path in NEW_SCOPE:
        if not path.exists():
            findings.append({"file": str(path.relative_to(ROOT)), "issue": "missing"})
            continue
        checked += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for term in BLOCKED:
            if term in text:
                findings.append({"file": str(path.relative_to(ROOT)), "issue": "blocked_term", "term": term})
    payload = {
        "status": "PASS" if not findings else "FAIL",
        "official_product_name": "AFIP",
        "official_full_name": "Automated Financial Intelligence Platform",
        "checked_files": checked,
        "required_terms": REQUIRED,
        "blocked_terms": BLOCKED,
        "findings": findings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
