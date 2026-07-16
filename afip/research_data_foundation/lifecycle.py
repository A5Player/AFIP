from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any, Mapping

CHECKPOINTS = {"M15": timedelta(minutes=15), "M30": timedelta(minutes=30), "H1": timedelta(hours=1), "H4": timedelta(hours=4), "D1": timedelta(days=1)}


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def checkpoint_plan(execution_utc: str) -> dict[str, Any]:
    base = _utc(execution_utc)
    return {name: {"status": "PENDING", "scheduled_at_utc": (base + offset).isoformat(), "observed_at_utc": None,
                   "market_snapshot": None, "assessment": None,
                   "leakage_policy": "OBSERVE_ONLY_AT_OR_AFTER_SCHEDULED_TIME"} for name, offset in CHECKPOINTS.items()}


@dataclass(frozen=True)
class GateRecord:
    gate: str
    outcome: str
    current_value: Any
    threshold: Any
    reason: str
    observed_at_utc: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TradeLifecycleRecorder:
    """Research-only updater for complete trade-case lifecycle files."""

    def __init__(self, cases_directory: Path | str = Path("runtime/research/trade_cases")) -> None:
        self.cases_directory = Path(cases_directory)

    def _path(self, trade_case_id: str) -> Path:
        return self.cases_directory / f"{trade_case_id}.json"

    def load(self, trade_case_id: str) -> dict[str, Any]:
        return json.loads(self._path(trade_case_id).read_text(encoding="utf-8"))

    def save(self, case: Mapping[str, Any]) -> Path:
        path = self._path(str(case["trade_case_id"]))
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(dict(case), indent=2, sort_keys=True, default=str), encoding="utf-8")
        temporary.replace(path)
        return path

    def append_gate(self, trade_case_id: str, gate: GateRecord) -> dict[str, Any]:
        case = self.load(trade_case_id)
        trace = dict(case.get("decision_trace", {}))
        gates = list(trace.get("gates", ()))
        gates.append(gate.as_dict())
        trace["gates"] = gates
        case["decision_trace"] = trace
        case["updated_at_utc"] = gate.observed_at_utc
        self.save(case)
        return case

    def append_holding(self, trade_case_id: str, observation: Mapping[str, Any]) -> dict[str, Any]:
        case = self.load(trade_case_id)
        timeline = list(case.get("holding_timeline", ()))
        timeline.append(dict(observation))
        case["holding_timeline"] = timeline
        case["updated_at_utc"] = str(observation.get("observed_at_utc", case.get("updated_at_utc")))
        self.save(case)
        return case

    def record_exit(self, trade_case_id: str, exit_context: Mapping[str, Any]) -> dict[str, Any]:
        case = self.load(trade_case_id)
        case["exit_context"] = dict(exit_context)
        case["lifecycle_state"] = "CLOSED_POST_TRADE_OBSERVATION_PENDING"
        case["updated_at_utc"] = str(exit_context.get("observed_at_utc", case.get("updated_at_utc")))
        self.save(case)
        return case

    def observe_checkpoint(self, trade_case_id: str, checkpoint: str, *, observed_at_utc: str,
                           market_snapshot: Mapping[str, Any], assessment: Mapping[str, Any]) -> dict[str, Any]:
        name = checkpoint.upper()
        if name not in CHECKPOINTS:
            raise ValueError(f"unsupported_checkpoint:{checkpoint}")
        case = self.load(trade_case_id)
        plans = dict(case.get("post_trade_checkpoints") or checkpoint_plan(case["created_at_utc"]))
        scheduled = _utc(plans[name]["scheduled_at_utc"])
        observed = _utc(observed_at_utc)
        if observed < scheduled:
            raise ValueError("future_data_leakage_blocked:checkpoint_not_due")
        plans[name] = {**plans[name], "status": "COMPLETED", "observed_at_utc": observed.isoformat(),
                       "market_snapshot": dict(market_snapshot), "assessment": dict(assessment)}
        case["post_trade_checkpoints"] = plans
        case["updated_at_utc"] = observed.isoformat()
        if all(item.get("status") == "COMPLETED" for item in plans.values()):
            case["lifecycle_state"] = "COMPLETE"
        self.save(case)
        return case
