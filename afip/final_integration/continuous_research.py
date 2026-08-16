"""Incremental A29-A36 orchestration owned by the canonical research service."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Callable

from .io import atomic_json, read_json, utc_now


class ContinuousResearchPipeline:
    """Run persisted research stages only when their closed evidence changes.

    This class never imports MT5 and never calls execution.  Market collection
    remains owned by the existing Phase V research authority.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.state_path = self.root / "runtime/research/a37_continuous_research_status.json"
        self.lock_path = self.root / "runtime/control/final_integration/a37_research_cycle.lock"
        self.config_path = self.root / "config/a37_continuous_research.json"

    def config(self) -> dict[str, Any]:
        value = {"enabled": True, "minimum_heavy_interval_seconds": 3600,
                 "run_a31": True, "run_a32_a33": True, "run_a35": True,
                 "run_a36_offline_analysis": True}
        if self.config_path.exists():
            loaded = json.loads(self.config_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                value.update(loaded)
        return value

    def _signature(self, paths: list[Path]) -> str:
        digest = hashlib.sha256()
        for path in sorted(paths):
            if path.is_file():
                stat = path.stat()
                digest.update(str(path.relative_to(self.root)).encode())
                digest.update(f"{stat.st_size}:{stat.st_mtime_ns}".encode())
        return digest.hexdigest()

    def _inputs(self) -> dict[str, list[Path]]:
        research = self.root / "runtime/research"
        automatic = research / "automatic/schema_v2"
        lake = list((research / "historical_data_lake").rglob("records.jsonl"))
        automatic_inputs = [automatic / "candidates.jsonl",
                            automatic / "adversarial_market_behaviour/outcomes.jsonl", *lake]
        return {
            "A30": automatic_inputs[:2],
            "A31": [research / "a22_holding_exit_validation_observations.jsonl"],
            "A32_A33": automatic_inputs,
            "A35": automatic_inputs,
            "A36": [research / "a36_cross_market_capital/a36_collection.json",
                    *list((research / "a36_cross_market_capital/bars").glob("*_H1.json")),
                    research / "a35_atr_buffer/a35_atr_buffer_campaign.json"],
            "A38": [research / "a32_real_backtest/a32_real_backtest_campaign.json",
                    research / "a33_multi_objective_ranking/a33_multi_objective_ranking.json",
                    research / "a35_atr_buffer/a35_atr_buffer_campaign.json",
                    research / "a36_cross_market_capital/a36_cross_market_capital_report.json"],
            "A39": [research / "a33_multi_objective_ranking/a33_multi_objective_ranking.json"],
            "A41": [automatic / "snapshots.jsonl", automatic / "candidates.jsonl",
                    research / "a20_holding_exit_observations.jsonl"],
            "A40": [research / "a22_holding_exit_validation_observations.jsonl"],
            "A42": [research / "a40_time_session_outcomes/a40_normalized_closed_outcomes.jsonl"],
        }

    def _acquire(self) -> bool:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if self.lock_path.exists() and time.time() - self.lock_path.stat().st_mtime > 7200:
            self.lock_path.unlink(missing_ok=True)
        try:
            descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(descriptor, "w") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "started_at_utc": utc_now()}))
        return True

    def _stage(self, name: str, function: Callable[[], Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            result = function()
            status = str(result.get("status", "PASS")) if isinstance(result, dict) else "PASS"
            return {"stage": name, "status": status, "duration_seconds": round(time.perf_counter()-started, 3)}
        except FileNotFoundError as exc:
            return {"stage": name, "status": "WAITING_FOR_INPUT", "reason": str(exc),
                    "duration_seconds": round(time.perf_counter()-started, 3)}
        except Exception as exc:
            return {"stage": name, "status": "ERROR", "reason": f"{type(exc).__name__}: {exc}",
                    "duration_seconds": round(time.perf_counter()-started, 3)}

    def run_once(self) -> dict[str, Any]:
        config = self.config()
        if not bool(config.get("enabled", True)):
            return {"status": "DISABLED", "execution_authority": "NONE", "orders_sent": False}
        if not self._acquire():
            return {"status": "SKIPPED_ALREADY_RUNNING", "execution_authority": "NONE", "orders_sent": False}
        try:
            previous = read_json(self.state_path)
            previous_signatures = previous.get("input_signatures", {}) if isinstance(previous, dict) else {}
            inputs = self._inputs()
            signatures = {name: self._signature(paths) for name, paths in inputs.items()}
            now = time.time()
            last_heavy = float(previous.get("last_heavy_epoch", 0) or 0)
            heavy_due = now - last_heavy >= max(300, int(config["minimum_heavy_interval_seconds"]))
            stages: list[dict[str, Any]] = []

            if signatures["A30"] != previous_signatures.get("A30"):
                from tools.afip_a30_research_decision_matrix import build_report
                def a30() -> dict[str, Any]:
                    result = build_report(self.root); path = self.root / "runtime/research/a30_research_decision_matrix.json"
                    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
                    return result
                stages.append(self._stage("A30_DECISION_MATRIX", a30))

            if config.get("run_a31") and signatures["A31"] != previous_signatures.get("A31"):
                from tools.afip_a31_daily_participation_research import build
                def a31() -> dict[str, Any]:
                    result = build(self.root); path = self.root / "runtime/research/a31_daily_participation_report.json"
                    path.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8"); return result
                stages.append(self._stage("A31_DAILY_PARTICIPATION", a31))

            ran_heavy = False
            if heavy_due and config.get("run_a32_a33") and signatures["A32_A33"] != previous_signatures.get("A32_A33"):
                from tools.afip_a32_real_backtest_campaign import run_campaign, write_outputs
                from tools.afip_a33_multi_objective_ranking import build_report, write_outputs as write_a33
                def a32_a33() -> dict[str, Any]:
                    a32 = run_campaign(self.root); write_outputs(a32, self.root / "runtime/research/a32_real_backtest")
                    a33 = build_report(a32); write_a33(a33, self.root / "runtime/research/a33_multi_objective_ranking")
                    return {"status": "PASS", "a32_rows": len(a32.get("rows", [])), "a33_eligible": a33.get("eligible_rows", 0)}
                stages.append(self._stage("A32_A33_BACKTEST_RANKING", a32_a33)); ran_heavy = True

            if heavy_due and config.get("run_a35") and signatures["A35"] != previous_signatures.get("A35"):
                from tools.afip_a35_atr_buffer_campaign import run_campaign, write_outputs
                def a35() -> dict[str, Any]:
                    result = run_campaign(self.root); write_outputs(result, self.root / "runtime/research/a35_atr_buffer")
                    return {"status": "PASS", "rows": len(result.get("rows", [])),
                            "eligible": result.get("eligible_research_rows", 0)}
                stages.append(self._stage("A35_ATR_BUFFER", a35)); ran_heavy = True

            if config.get("run_a36_offline_analysis") and signatures["A36"] != previous_signatures.get("A36"):
                from tools.afip_a36_cross_market_capital import analyze
                stages.append(self._stage("A36_OFFLINE_CROSS_MARKET", lambda: analyze(self.root)))

            # Recalculate the signature after upstream stages may have written reports.
            a38_signature = self._signature(inputs["A38"])
            signatures["A38"] = a38_signature
            if a38_signature != previous_signatures.get("A38"):
                from tools.afip_a38_research_readiness_gate import build_report, write_outputs
                def a38() -> dict[str, Any]:
                    result = build_report(self.root)
                    write_outputs(result, self.root)
                    return result
                stages.append(self._stage("A38_RESEARCH_READINESS", a38))

            a39_signature = self._signature(inputs["A39"])
            signatures["A39"] = a39_signature
            if a39_signature != previous_signatures.get("A39"):
                from tools.afip_a39_a33_blocker_diagnostics import build_report, write_outputs
                def a39() -> dict[str, Any]:
                    result = build_report(self.root)
                    write_outputs(result, self.root)
                    return result
                stages.append(self._stage("A39_A33_BLOCKER_DIAGNOSTICS", a39))

            if signatures["A41"] != previous_signatures.get("A41"):
                from tools.afip_a41_historical_closed_outcome_bridge import build_report, write_outputs
                def a41() -> dict[str, Any]:
                    result = build_report(self.root); write_outputs(result, self.root); return result
                stages.append(self._stage("A41_HISTORICAL_CLOSED_OUTCOME_BRIDGE", a41))

            # A41 may have appended A22 outcomes in this cycle.
            signatures["A40"] = self._signature(inputs["A40"])
            if signatures["A40"] != previous_signatures.get("A40"):
                from tools.afip_a40_time_session_outcome_foundation import build_report, write_outputs
                def a40() -> dict[str, Any]:
                    result = build_report(self.root); write_outputs(result, self.root); return result
                stages.append(self._stage("A40_TIME_SESSION_FOUNDATION", a40))

            # A40 may have atomically refreshed the normalized candidate-group source.
            signatures["A42"] = self._signature(inputs["A42"])
            if signatures["A42"] != previous_signatures.get("A42"):
                from tools.afip_a42_selective_trading_rankings import build_report, write_outputs
                def a42() -> dict[str, Any]:
                    result = build_report(self.root); write_outputs(result, self.root); return result
                stages.append(self._stage("A42_SELECTIVE_TRADING_RANKINGS", a42))

            from tools.afip_a29_research_pipeline_coverage import build_report as a29_report
            def a29() -> dict[str, Any]:
                result = a29_report(self.root); path = self.root / "runtime/research/a29_research_pipeline_coverage.json"
                path.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8"); return result
            stages.append(self._stage("A29_COVERAGE", a29))

            payload = {"schema": "afip.a37.continuous_research.v1", "status": "READY",
                       "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                       "cycle_result": "UPDATED" if any(x["status"] not in {"WAITING_FOR_INPUT"} for x in stages[:-1]) else "NO_NEW_EVIDENCE",
                       "stages": stages, "input_signatures": signatures,
                       "last_heavy_epoch": now if ran_heavy else last_heavy,
                       "profile_strategy_selection": "NOT_DECIDED", "automatic_profile_assignment": False,
                       "execution_authority": "NONE", "orders_sent": False,
                       "mt5_collection_authority": "EXISTING_PHASE_V_ONLY"}
            atomic_json(self.state_path, payload)
            return payload
        finally:
            self.lock_path.unlink(missing_ok=True)
