from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .lifecycle import TradeLifecycleRecorder
from .recorder import ResearchRecorder


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RuntimeCollectionSummary:
    scanned_profiles: int
    accepted_events: int
    duplicate_events: int
    trade_cases_written: int
    holding_observations: int
    exits_recorded: int
    checkpoints_recorded: int
    status: str = "READY"
    research_only: bool = True
    affects_trading: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchRuntimeCollector:
    """Research-only bridge from production runtime artifacts to Trade Cases.

    It never imports or invokes order placement code. Inputs are append-only
    ledgers and observation payloads supplied by an external observer.
    """

    def __init__(self, root: Path | str = Path("runtime/research")) -> None:
        self.root = Path(root)
        self.recorder = ResearchRecorder(self.root)
        self.lifecycle = TradeLifecycleRecorder(self.root / "trade_cases")
        self.summary_path = self.root / "runtime_collection_summary.json"

    @staticmethod
    def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(dict(payload), indent=2, sort_keys=True, default=str), encoding="utf-8")
        temporary.replace(path)

    def ingest_ledgers(self, ledger_paths: Iterable[Path | str]) -> RuntimeCollectionSummary:
        accepted = duplicates = cases = scanned = 0
        for raw_path in ledger_paths:
            path = Path(raw_path)
            if not path.exists():
                continue
            result = self.recorder.ingest_ledger(path)
            scanned += 1
            accepted += result.accepted_events
            duplicates += result.duplicate_events
            cases += result.trade_cases_written
        summary = RuntimeCollectionSummary(scanned, accepted, duplicates, cases, 0, 0, 0)
        self._write_json(self.summary_path, {**summary.as_dict(), "updated_at_utc": _utc_now()})
        return summary

    def _case_for_ticket(self, ticket: int) -> dict[str, Any] | None:
        for path in sorted((self.root / "trade_cases").glob("CASE-*.json")):
            try:
                case = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if int(ticket) in {int(value) for value in case.get("tickets", ())}:
                return case
        return None

    def record_position_observation(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        ticket = int(observation.get("ticket", 0) or 0)
        case = self._case_for_ticket(ticket)
        if case is None:
            raise KeyError(f"trade_case_not_found_for_ticket:{ticket}")
        timeline = list(case.get("holding_timeline", ()))
        floating = float(observation.get("floating_profit", observation.get("profit", 0.0)) or 0.0)
        previous_mfe = max((float(item.get("mfe", 0.0) or 0.0) for item in timeline), default=0.0)
        previous_mae = min((float(item.get("mae", 0.0) or 0.0) for item in timeline), default=0.0)
        normalized = dict(observation)
        normalized.setdefault("observed_at_utc", _utc_now())
        normalized["floating_profit"] = max(0.0, floating)
        normalized["floating_loss"] = min(0.0, floating)
        normalized["mfe"] = max(previous_mfe, floating, 0.0)
        normalized["mae"] = min(previous_mae, floating, 0.0)
        normalized["research_only"] = True
        normalized["affects_trading"] = False
        return self.lifecycle.append_holding(case["trade_case_id"], normalized)

    def record_closed_trade(self, exit_payload: Mapping[str, Any]) -> dict[str, Any]:
        ticket = int(exit_payload.get("ticket", 0) or 0)
        case = self._case_for_ticket(ticket)
        if case is None:
            raise KeyError(f"trade_case_not_found_for_ticket:{ticket}")
        timeline = list(case.get("holding_timeline", ()))
        mfe = max((float(item.get("mfe", 0.0) or 0.0) for item in timeline), default=0.0)
        mae = min((float(item.get("mae", 0.0) or 0.0) for item in timeline), default=0.0)
        realized = float(exit_payload.get("realized_profit", exit_payload.get("profit", 0.0)) or 0.0)
        normalized = dict(exit_payload)
        normalized.setdefault("observed_at_utc", _utc_now())
        normalized.setdefault("exit_reason", "BROKER_CLOSED_POSITION")
        normalized["mfe"] = mfe
        normalized["mae"] = mae
        normalized["profit_retained"] = realized
        normalized["profit_given_back"] = max(0.0, mfe - realized)
        normalized["research_only"] = True
        normalized["affects_trading"] = False
        return self.lifecycle.record_exit(case["trade_case_id"], normalized)

    def record_checkpoint(self, ticket: int, checkpoint: str, *, observed_at_utc: str,
                          market_snapshot: Mapping[str, Any], assessment: Mapping[str, Any]) -> dict[str, Any]:
        case = self._case_for_ticket(ticket)
        if case is None:
            raise KeyError(f"trade_case_not_found_for_ticket:{ticket}")
        return self.lifecycle.observe_checkpoint(case["trade_case_id"], checkpoint,
            observed_at_utc=observed_at_utc, market_snapshot=market_snapshot,
            assessment={**dict(assessment), "research_only": True, "affects_trading": False})
