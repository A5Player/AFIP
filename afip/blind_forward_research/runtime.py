"""Deterministic, execution-neutral blind-forward research for AFIP.

The engine evaluates configured TP/SL/time-exit candidates against bars strictly
later than the entry observation.  It has no broker or order authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _utc(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamps must include timezone")
    return dt.astimezone(timezone.utc)


def deterministic_input_hash(value: Mapping[str, Any]) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ForwardBar:
    closed_at_utc: str
    open: float
    high: float
    low: float
    close: float

    def validate(self) -> None:
        _utc(self.closed_at_utc)
        values = (self.open, self.high, self.low, self.close)
        if not all(isinstance(v, (int, float)) for v in values):
            raise ValueError("bar OHLC values must be numeric")
        if self.low > self.high:
            raise ValueError("bar low must not exceed high")
        if not self.low <= self.open <= self.high or not self.low <= self.close <= self.high:
            raise ValueError("bar open and close must be inside low/high")


@dataclass(frozen=True)
class CandidateSet:
    candidate_set_id: str
    version: str
    take_profit_points: tuple[int, ...]
    stop_loss_points: tuple[int, ...]
    time_exit_bars: tuple[int, ...]
    same_bar_resolution: str = "SL_FIRST"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CandidateSet":
        obj = cls(
            candidate_set_id=str(value["candidate_set_id"]),
            version=str(value["version"]),
            take_profit_points=tuple(int(x) for x in value["take_profit_points"]),
            stop_loss_points=tuple(int(x) for x in value["stop_loss_points"]),
            time_exit_bars=tuple(int(x) for x in value.get("time_exit_bars", ())),
            same_bar_resolution=str(value.get("same_bar_resolution", "SL_FIRST")),
        )
        obj.validate()
        return obj

    def validate(self) -> None:
        if not self.candidate_set_id or not self.version:
            raise ValueError("candidate set identity and version are required")
        if not self.take_profit_points or not self.stop_loss_points:
            raise ValueError("at least one TP and SL candidate are required")
        if any(x <= 0 for x in self.take_profit_points + self.stop_loss_points + self.time_exit_bars):
            raise ValueError("candidate values must be positive")
        if len(set(self.take_profit_points)) != len(self.take_profit_points):
            raise ValueError("duplicate TP candidate")
        if len(set(self.stop_loss_points)) != len(self.stop_loss_points):
            raise ValueError("duplicate SL candidate")
        if self.same_bar_resolution != "SL_FIRST":
            raise ValueError("only conservative SL_FIRST resolution is certified")


@dataclass(frozen=True)
class ResearchCase:
    case_id: str
    instrument: str
    timeframe: str
    direction: str
    entry_price: float
    point_size: float
    entry_at_utc: str
    market_regime: str
    pattern_family: str
    features: Mapping[str, Any]
    provenance: Mapping[str, Any]
    data_quality: Mapping[str, Any]

    def validate(self) -> None:
        if self.direction not in {"BUY", "SELL"}:
            raise ValueError("direction must be BUY or SELL")
        if self.entry_price <= 0 or self.point_size <= 0:
            raise ValueError("entry_price and point_size must be positive")
        _utc(self.entry_at_utc)
        if bool(self.provenance.get("future_data_used", False)):
            raise ValueError("future data is forbidden")


@dataclass(frozen=True)
class CandidateOutcome:
    take_profit_points: int
    stop_loss_points: int
    time_exit_bars: int | None
    outcome: str
    exit_reason: str
    exit_price: float
    exit_at_utc: str
    holding_bars: int
    holding_seconds: int
    maximum_favorable_excursion_points: float
    maximum_adverse_excursion_points: float
    result_points: float
    same_bar_collision: bool


@dataclass(frozen=True)
class BlindForwardResult:
    schema_version: str
    result_id: str
    input_hash: str
    case_id: str
    candidate_set_id: str
    candidate_set_version: str
    research_eligibility: str
    quarantine_reasons: tuple[str, ...]
    execution_authority: str
    evaluated_bar_count: int
    outcomes: tuple[CandidateOutcome, ...]
    evaluated_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BlindForwardResearchEngine:
    """Evaluate candidate outcomes using only closed bars after entry time."""

    def evaluate(
        self,
        case: ResearchCase,
        candidate_set: CandidateSet,
        bars: Sequence[ForwardBar],
    ) -> BlindForwardResult:
        case.validate()
        candidate_set.validate()
        entry_time = _utc(case.entry_at_utc)
        normalized: list[ForwardBar] = []
        prior: datetime | None = None
        for bar in bars:
            bar.validate()
            close_time = _utc(bar.closed_at_utc)
            if close_time <= entry_time:
                raise ValueError("blind-forward bars must close strictly after entry")
            if prior is not None and close_time <= prior:
                raise ValueError("blind-forward bars must be strictly chronological")
            prior = close_time
            normalized.append(bar)

        reasons = self._quarantine_reasons(case, normalized)
        eligibility = "ELIGIBLE" if not reasons else "QUARANTINED"
        stable_input = {
            "schema_version": "blind-forward-input.v1",
            "case": asdict(case),
            "candidate_set": asdict(candidate_set),
            "bars": [asdict(x) for x in normalized],
        }
        input_hash = deterministic_input_hash(stable_input)
        outcomes: tuple[CandidateOutcome, ...] = ()
        if eligibility == "ELIGIBLE":
            outcomes = tuple(
                self._evaluate_candidate(case, normalized, tp, sl, time_exit)
                for tp in candidate_set.take_profit_points
                for sl in candidate_set.stop_loss_points
                for time_exit in ((None,) + candidate_set.time_exit_bars)
            )
        stable_result = {
            "input_hash": input_hash,
            "case_id": case.case_id,
            "candidate_set_id": candidate_set.candidate_set_id,
            "candidate_set_version": candidate_set.version,
            "research_eligibility": eligibility,
            "quarantine_reasons": reasons,
            "execution_authority": "NONE",
            "evaluated_bar_count": len(normalized),
            "outcomes": [asdict(x) for x in outcomes],
        }
        result_id = deterministic_input_hash(stable_result)
        return BlindForwardResult(
            schema_version="blind-forward-result.v1",
            result_id=result_id,
            input_hash=input_hash,
            case_id=case.case_id,
            candidate_set_id=candidate_set.candidate_set_id,
            candidate_set_version=candidate_set.version,
            research_eligibility=eligibility,
            quarantine_reasons=tuple(reasons),
            execution_authority="NONE",
            evaluated_bar_count=len(normalized),
            outcomes=outcomes,
            evaluated_at_utc=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _quarantine_reasons(case: ResearchCase, bars: Sequence[ForwardBar]) -> list[str]:
        reasons: list[str] = []
        if not bars:
            reasons.append("NO_FORWARD_BARS")
        if str(case.data_quality.get("status", "")).upper() != "PASS":
            reasons.append("DATA_QUALITY_NOT_PASS")
        if not case.market_regime:
            reasons.append("MARKET_REGIME_MISSING")
        if not case.pattern_family:
            reasons.append("PATTERN_FAMILY_MISSING")
        if not case.features:
            reasons.append("FEATURES_MISSING")
        return reasons

    @staticmethod
    def _evaluate_candidate(
        case: ResearchCase,
        bars: Sequence[ForwardBar],
        tp_points: int,
        sl_points: int,
        time_exit_bars: int | None,
    ) -> CandidateOutcome:
        sign = 1.0 if case.direction == "BUY" else -1.0
        tp_price = case.entry_price + sign * tp_points * case.point_size
        sl_price = case.entry_price - sign * sl_points * case.point_size
        mfe = 0.0
        mae = 0.0
        selected_bar = bars[-1]
        exit_price = selected_bar.close
        exit_reason = "END_OF_AVAILABLE_DATA"
        collision = False
        holding_bars = len(bars)

        for index, bar in enumerate(bars, start=1):
            favorable = (bar.high - case.entry_price) / case.point_size if sign > 0 else (case.entry_price - bar.low) / case.point_size
            adverse = (case.entry_price - bar.low) / case.point_size if sign > 0 else (bar.high - case.entry_price) / case.point_size
            mfe = max(mfe, favorable)
            mae = max(mae, adverse)
            tp_hit = bar.high >= tp_price if sign > 0 else bar.low <= tp_price
            sl_hit = bar.low <= sl_price if sign > 0 else bar.high >= sl_price
            if tp_hit and sl_hit:
                selected_bar, exit_price, exit_reason, collision, holding_bars = bar, sl_price, "STOP_LOSS", True, index
                break
            if sl_hit:
                selected_bar, exit_price, exit_reason, holding_bars = bar, sl_price, "STOP_LOSS", index
                break
            if tp_hit:
                selected_bar, exit_price, exit_reason, holding_bars = bar, tp_price, "TAKE_PROFIT", index
                break
            if time_exit_bars is not None and index >= time_exit_bars:
                selected_bar, exit_price, exit_reason, holding_bars = bar, bar.close, "TIME_EXIT", index
                break

        result_points = sign * (exit_price - case.entry_price) / case.point_size
        outcome = "WIN" if result_points > 0 else "LOSS" if result_points < 0 else "FLAT"
        holding_seconds = int((_utc(selected_bar.closed_at_utc) - _utc(case.entry_at_utc)).total_seconds())
        return CandidateOutcome(
            take_profit_points=tp_points,
            stop_loss_points=sl_points,
            time_exit_bars=time_exit_bars,
            outcome=outcome,
            exit_reason=exit_reason,
            exit_price=round(exit_price, 10),
            exit_at_utc=_utc(selected_bar.closed_at_utc).isoformat(),
            holding_bars=holding_bars,
            holding_seconds=holding_seconds,
            maximum_favorable_excursion_points=round(mfe, 8),
            maximum_adverse_excursion_points=round(mae, 8),
            result_points=round(result_points, 8),
            same_bar_collision=collision,
        )


@dataclass(frozen=True)
class ResearchWriteResult:
    status: str
    result_id: str
    relative_path: str
    checksum_sha256: str
    duplicate: bool


class BlindForwardResultStore:
    """Append-only JSONL store; duplicates are skipped by deterministic ID."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def append(self, result: BlindForwardResult) -> ResearchWriteResult:
        evaluated = _utc(result.evaluated_at_utc)
        relative = Path(f"year={evaluated:%Y}", f"month={evaluated:%m}", f"day={evaluated:%d}", "blind_forward_results.jsonl")
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        index = path.with_name("result_ids.txt")
        existing = set(index.read_text(encoding="utf-8").splitlines()) if index.exists() else set()
        if result.result_id in existing:
            return ResearchWriteResult("DUPLICATE_SKIPPED", result.result_id, relative.as_posix(), "", True)
        line = canonical_json(result.to_dict()) + "\n"
        encoded = line.encode("utf-8")
        with path.open("ab") as stream:
            stream.write(encoded)
            stream.flush()
        with index.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(result.result_id + "\n")
        checksum = sha256(encoded).hexdigest()
        manifest = {
            "result_id": result.result_id,
            "input_hash": result.input_hash,
            "checksum_sha256": checksum,
            "relative_path": relative.as_posix(),
            "research_eligibility": result.research_eligibility,
            "execution_authority": result.execution_authority,
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        with path.with_name("manifest.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(manifest) + "\n")
        return ResearchWriteResult("APPENDED", result.result_id, relative.as_posix(), checksum, False)


def load_candidate_set(path: str | Path) -> CandidateSet:
    return CandidateSet.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))
