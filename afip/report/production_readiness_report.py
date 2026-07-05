"""Production readiness report for AFIP Pack 16."""
from __future__ import annotations


class ProductionReadinessReport:
    """Create a compact production readiness summary."""

    name = "ProductionReadinessReport"

    def build(self, checks: list[dict]) -> dict:
        if not checks:
            return {"status": "LEARNING", "score": 0.0, "passed": 0, "failed": 0, "items": []}
        passed = [check for check in checks if check.get("status") in {"READY", "PASS"} and check.get("action") != "WAIT"]
        failed = [check for check in checks if check.get("status") in {"BLOCKED", "FAIL"}]
        score = round(len(passed) / len(checks) * 100.0 - len(failed) * 10.0, 2)
        status = "PASS" if score >= 80.0 and not failed else "CAUTION" if score >= 60.0 else "FAIL"
        return {"status": status, "score": max(0.0, score), "passed": len(passed), "failed": len(failed), "items": checks}
