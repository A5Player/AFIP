"""Walk-forward validation engine for out-of-sample stability checks."""
from __future__ import annotations


class WalkForwardEngine:
    """Evaluate train/test windows without relying on future data."""

    name = "WalkForwardEngine"

    def evaluate(self, windows: list[dict]) -> dict:
        if not windows:
            return {"name": self.name, "status": "NO_DATA", "score": 0.0, "reason": "no_windows", "windows": []}
        reviewed = []
        passed = 0
        for index, window in enumerate(windows, start=1):
            train = float(window.get("train_score", 0.0) or 0.0)
            test = float(window.get("test_score", 0.0) or 0.0)
            degradation = max(0.0, train - test)
            stable = test >= 55.0 and degradation <= 20.0
            passed += 1 if stable else 0
            reviewed.append({
                "window": index,
                "train_score": round(train, 2),
                "test_score": round(test, 2),
                "degradation": round(degradation, 2),
                "stable": stable,
            })
        pass_rate = round(passed * 100.0 / len(reviewed), 2)
        status = "READY" if pass_rate >= 60.0 else "CAUTION"
        return {"name": self.name, "status": status, "score": pass_rate, "reason": "walk_forward_ready", "windows": reviewed, "pass_rate": pass_rate}
