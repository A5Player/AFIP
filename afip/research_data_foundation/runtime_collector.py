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

    def ingest_ledgers(
        self, ledger_paths: Iterable[Path | str],
        activation_ledger_paths: Iterable[Path | str] = (),
    ) -> RuntimeCollectionSummary:
        accepted = duplicates = cases = scanned = holding = exits = 0
        for raw_path in ledger_paths:
            path = Path(raw_path)
            if not path.exists():
                continue
            result = self.recorder.ingest_ledger(path)
            scanned += 1
            accepted += result.accepted_events
            duplicates += result.duplicate_events
            cases += result.trade_cases_written
        for raw_path in activation_ledger_paths:
            path = Path(raw_path)
            if not path.exists():
                continue
            scanned += 1
            result = self._ingest_activation_ledger(path)
            accepted += result["accepted"]
            duplicates += result["duplicates"]
            holding += result["holding"]
            exits += result["exits"]
        summary = RuntimeCollectionSummary(scanned, accepted, duplicates, cases, holding, exits, 0)
        self._write_json(self.summary_path, {**summary.as_dict(), "updated_at_utc": _utc_now()})
        return summary


    def _bridge_state(self) -> set[str]:
        path = self.root / "runtime_bridge_event_ids.json"
        try:
            values = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return set()
        return {str(value) for value in values if value}

    def _save_bridge_state(self, values: set[str]) -> None:
        self._write_json(self.root / "runtime_bridge_event_ids.json", {"event_ids": sorted(values)})

    @staticmethod
    def _activation_event_id(path: Path, line_number: int, payload: Mapping[str, Any]) -> str:
        import hashlib
        canonical = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(f"{path}|{line_number}|{canonical}".encode("utf-8")).hexdigest()

    def _ingest_activation_ledger(self, path: Path) -> dict[str, int]:
        state_path = self.root / "runtime_bridge_event_ids.json"
        try:
            raw_state = json.loads(state_path.read_text(encoding="utf-8"))
            seen = {str(value) for value in raw_state.get("event_ids", ())}
        except (OSError, ValueError, TypeError):
            seen = set()
        accepted = duplicates = holding = exits = 0
        for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
            except (ValueError, TypeError):
                continue
            event_id = self._activation_event_id(path, line_number, payload)
            if event_id in seen:
                duplicates += 1
                continue
            event = str(payload.get("event", "")).upper()
            try:
                if event == "POSITION_CARE":
                    snapshot = dict(payload.get("position_snapshot", {}))
                    observation = {
                        **snapshot,
                        "ticket": int(payload.get("ticket", snapshot.get("ticket", 0)) or 0),
                        "floating_profit": float(snapshot.get("unrealized_profit", 0.0) or 0.0),
                        "execution_trace_id": payload.get("execution_trace_id", ""),
                        "position_care": payload.get("position_care", {}),
                        "intelligence_context": payload.get("intelligence_context", {}),
                        "observed_at_utc": snapshot.get("observed_at", payload.get("updated_at_utc", _utc_now())),
                    }
                    self.record_position_observation(observation)
                    holding += 1
                elif event == "POSITION_CLOSED":
                    self.record_closed_trade(payload)
                    exits += 1
                else:
                    continue
            except (KeyError, ValueError, TypeError):
                # The execution event may not have been collected yet. Leave the
                # activation event uncommitted so a later cycle can retry it.
                continue
            seen.add(event_id)
            accepted += 1
        self._write_json(state_path, {"event_ids": sorted(seen), "updated_at_utc": _utc_now()})
        return {"accepted": accepted, "duplicates": duplicates, "holding": holding, "exits": exits}

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

        # Preserve broker-reported money truth. MT5 commission/swap/fee values are
        # normally signed (costs are negative), so they are added to gross profit.
        commission = float(exit_payload.get("commission", 0.0) or 0.0)
        swap = float(exit_payload.get("swap", 0.0) or 0.0)
        fee = float(exit_payload.get("fee", 0.0) or 0.0)
        explicit_net = exit_payload.get("net_profit")
        net_profit = float(explicit_net) if explicit_net is not None else realized + commission + swap + fee
        initial_risk = exit_payload.get("initial_risk_usd")
        initial_risk_usd = float(initial_risk) if initial_risk not in (None, "") else None
        realized_r = (net_profit / initial_risk_usd) if initial_risk_usd and initial_risk_usd > 0.0 else None
        exit_efficiency = (net_profit / mfe) if mfe > 0.0 else None

        required = {
            "ticket": ticket > 0,
            "observed_at_utc": bool(normalized.get("observed_at_utc")),
            "exit_reason": bool(normalized.get("exit_reason")),
            "money_result": any(key in exit_payload for key in ("realized_profit", "profit", "net_profit")),
        }
        missing = sorted(key for key, ok in required.items() if not ok)
        quality = "COMPLETE" if not missing else "INCOMPLETE"
        feedback_eligible = quality == "COMPLETE" and bool(case.get("market_context", {}).get("pattern_id"))

        normalized["mfe"] = mfe
        normalized["mae"] = mae
        normalized["gross_realized_profit_usd"] = realized
        normalized["commission_usd"] = commission
        normalized["swap_usd"] = swap
        normalized["fee_usd"] = fee
        normalized["net_realized_profit_usd"] = round(net_profit, 8)
        normalized["initial_risk_usd"] = initial_risk_usd
        normalized["realized_r_multiple"] = round(realized_r, 8) if realized_r is not None else None
        normalized["exit_efficiency_ratio"] = round(exit_efficiency, 8) if exit_efficiency is not None else None
        normalized["profit_retained"] = net_profit
        normalized["profit_given_back"] = max(0.0, mfe - net_profit)
        normalized["outcome_class"] = "WIN" if net_profit > 0.0 else ("LOSS" if net_profit < 0.0 else "BREAKEVEN")
        normalized["outcome_data_quality"] = quality
        normalized["missing_outcome_fields"] = missing
        normalized["research_feedback_status"] = "ELIGIBLE" if feedback_eligible else "QUARANTINED"
        normalized["research_feedback_reason"] = "complete_closed_trade_evidence" if feedback_eligible else "incomplete_or_unclassified_closed_trade"
        normalized["accounting_basis"] = "BROKER_REPORTED_REALIZED_PLUS_SIGNED_COMMISSION_SWAP_FEE"
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
