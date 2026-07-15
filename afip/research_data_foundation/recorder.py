from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import POST_TRADE_CHECKPOINTS, ResearchEvent, TradeCase, utc_now


@dataclass(frozen=True)
class RecorderSummary:
    source_path: str
    scanned_lines: int
    accepted_events: int
    duplicate_events: int
    trade_cases_written: int
    rejected_lines: int
    output_directory: str
    status: str = "READY"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchRecorder:
    """Transforms append-only execution ledgers into versioned research files.

    The recorder is read-only with respect to trading. It only reads a ledger and
    writes research artifacts under its own output directory.
    """

    def __init__(self, output_directory: Path | str = Path("runtime/research")) -> None:
        self.output_directory = Path(output_directory)
        self.events_path = self.output_directory / "events" / "research_events.jsonl"
        self.cases_directory = self.output_directory / "trade_cases"
        self.rejections_path = self.output_directory / "rejections" / "rejected_lines.jsonl"
        self.index_path = self.output_directory / "research_index.json"

    @staticmethod
    def _canonical(payload: Mapping[str, Any]) -> str:
        return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _sha(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _safe_utc(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return utc_now()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            return utc_now()

    @staticmethod
    def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(dict(payload), sort_keys=True, default=str) + "\n")

    @staticmethod
    def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(dict(payload), indent=2, sort_keys=True, default=str), encoding="utf-8")
        temporary.replace(path)

    def _existing_event_ids(self) -> set[str]:
        if not self.events_path.exists():
            return set()
        ids: set[str] = set()
        for line in self.events_path.read_text(encoding="utf-8-sig").splitlines():
            try:
                value = json.loads(line)
                ids.add(str(value.get("event_id", "")))
            except (ValueError, TypeError):
                continue
        return ids

    def _event_from_ledger(
        self,
        payload: Mapping[str, Any],
        *,
        source_path: Path,
        line_number: int,
        raw_line: str,
    ) -> ResearchEvent:
        source_sha = self._sha(raw_line.rstrip("\r\n"))
        observed = self._safe_utc(payload.get("checked_at_utc"))
        profile = str(payload.get("profile_id", "UNKNOWN")).upper()
        symbol = str(payload.get("symbol", "GOLD#"))
        status = str(payload.get("status", "UNKNOWN")).upper()
        reason = str(payload.get("reason", "unknown"))
        event_type = "ORDER_EXECUTION" if status == "ORDER_SENT" else "DECISION_GATE"
        event_id = "EVT-" + self._sha(f"{source_path}|{line_number}|{source_sha}")[:24].upper()
        normalized_payload = dict(payload)
        normalized_payload["checked_at_utc"] = observed
        normalized_payload["gate_outcome"] = status
        normalized_payload["gate_reason"] = reason
        normalized_payload["recorded_without_execution_side_effect"] = True
        return ResearchEvent(
            event_id=event_id,
            event_type=event_type,
            observed_at_utc=observed,
            profile_id=profile,
            symbol=symbol,
            source_path=str(source_path),
            source_line_number=line_number,
            source_sha256=source_sha,
            payload=normalized_payload,
        )

    @staticmethod
    def _checkpoint_plan(execution_utc: str) -> dict[str, Any]:
        base = datetime.fromisoformat(execution_utc.replace("Z", "+00:00"))
        offsets = {
            "M30": timedelta(minutes=30),
            "H1": timedelta(hours=1),
            "H4": timedelta(hours=4),
            "D1": timedelta(days=1),
        }
        return {
            name: {
                "status": "PENDING",
                "scheduled_at_utc": (base + offsets[name]).astimezone(timezone.utc).isoformat(),
                "observed_at_utc": None,
                "market_snapshot": None,
                "leakage_policy": "OBSERVE_ONLY_AT_OR_AFTER_SCHEDULED_TIME",
            }
            for name in POST_TRADE_CHECKPOINTS
        }

    def _case_from_event(self, event: ResearchEvent) -> TradeCase | None:
        payload = dict(event.payload)
        tickets = tuple(int(v) for v in payload.get("tickets", ()) if int(v) > 0)
        if event.event_type != "ORDER_EXECUTION" or not tickets:
            return None
        case_key = f"{event.profile_id}|{event.symbol}|{','.join(map(str, tickets))}"
        case_id = "CASE-" + self._sha(case_key)[:24].upper()
        execution = {
            "status": payload.get("status"),
            "reason": payload.get("reason"),
            "allocated_lots": payload.get("allocated_lots", ()),
            "total_allocated_lot": payload.get("total_allocated_lot", 0.0),
            "order_check_called": payload.get("order_check_called", False),
            "order_send_called": payload.get("order_send_called", False),
            "mt5_result_code": payload.get("mt5_result_code"),
            "mt5_result_comment": payload.get("mt5_result_comment", ""),
            "tickets": tickets,
        }
        market = {
            "spread_points": payload.get("spread_points", 0.0),
            "caution_spread_points": payload.get("caution_spread_points", 0.0),
            "max_spread_points": payload.get("max_spread_points", 0.0),
            "trading_cost_status": payload.get("trading_cost_status", "UNKNOWN"),
            "point_size": payload.get("point_size", 0.0),
            "digits": payload.get("digits", 0),
        }
        decision_trace = {
            "action": payload.get("decision_action", "WAIT"),
            "confidence": payload.get("decision_confidence", 0.0),
            "risk_approved": payload.get("reason") != "risk_not_approved",
            "trading_cost_allowed": payload.get("trading_cost_allowed", False),
            "allocation_mode": payload.get("allocation_mode", "UNKNOWN"),
            "capital_tier": payload.get("current_tier_minimum_balance"),
            "target_tier_lots": payload.get("target_tier_lots", ()),
        }
        return TradeCase(
            trade_case_id=case_id,
            profile_id=event.profile_id,
            symbol=event.symbol,
            created_at_utc=event.observed_at_utc,
            updated_at_utc=event.observed_at_utc,
            lifecycle_state="OPEN_OR_SUBMITTED",
            decision_action=str(payload.get("decision_action", "WAIT")),
            decision_confidence=float(payload.get("decision_confidence", 0.0) or 0.0),
            order_status=str(payload.get("order_status", "DEMO_ORDER_SENT")),
            tickets=tickets,
            event_ids=(event.event_id,),
            market_context=market,
            decision_trace=decision_trace,
            execution_result=execution,
            post_trade_checkpoints=self._checkpoint_plan(event.observed_at_utc),
            data_lineage={
                "source_type": event.source_type,
                "source_path": event.source_path,
                "source_line_number": event.source_line_number,
                "source_sha256": event.source_sha256,
                "source_event_id": event.event_id,
            },
        )

    def ingest_ledger(self, ledger_path: Path | str) -> RecorderSummary:
        source = Path(ledger_path)
        if not source.exists():
            raise FileNotFoundError(f"ledger_not_found:{source}")
        existing = self._existing_event_ids()
        scanned = accepted = duplicates = cases = rejected = 0
        for line_number, raw in enumerate(source.read_text(encoding="utf-8-sig").splitlines(), start=1):
            scanned += 1
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
                if not isinstance(payload, Mapping):
                    raise TypeError("ledger_line_must_be_object")
                event = self._event_from_ledger(payload, source_path=source, line_number=line_number, raw_line=raw)
            except (ValueError, TypeError) as exc:
                rejected += 1
                self._append_jsonl(self.rejections_path, {
                    "source_path": str(source), "source_line_number": line_number,
                    "reason": f"{type(exc).__name__}:{exc}", "raw_sha256": self._sha(raw),
                    "rejected_at_utc": utc_now(),
                })
                continue
            if event.event_id in existing:
                duplicates += 1
                continue
            self._append_jsonl(self.events_path, event.as_dict())
            existing.add(event.event_id)
            accepted += 1
            trade_case = self._case_from_event(event)
            if trade_case is not None:
                self._write_json(self.cases_directory / f"{trade_case.trade_case_id}.json", trade_case.as_dict())
                cases += 1
        summary = RecorderSummary(
            source_path=str(source), scanned_lines=scanned, accepted_events=accepted,
            duplicate_events=duplicates, trade_cases_written=cases, rejected_lines=rejected,
            output_directory=str(self.output_directory),
        )
        self._write_json(self.index_path, {
            "status": summary.status,
            "updated_at_utc": utc_now(),
            "contract_version": "AFIP-RESEARCH-DATA-1.0",
            "latest_ingest": summary.as_dict(),
            "directories": {
                "events": str(self.events_path), "trade_cases": str(self.cases_directory),
                "rejections": str(self.rejections_path),
            },
        })
        return summary
