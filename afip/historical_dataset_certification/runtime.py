"""Historical dataset readiness certification for research-only AFIP use.

The certifier is execution-neutral. It never sends orders, changes position
sizing, or promotes research evidence into live authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REQUIRED_TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")
TIMEFRAME_SECONDS = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600, "H4": 14400, "D1": 86400}
STATUSES = ("READY", "CAUTION", "QUARANTINED")


def _utc(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(text)
    except ValueError:
        try:
            result = datetime.fromtimestamp(float(text), timezone.utc)
        except (TypeError, ValueError, OSError):
            return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def _timestamp(record: Mapping[str, Any]) -> datetime | None:
    for key in ("timestamp_utc", "time_utc", "datetime_utc", "timestamp", "time"):
        if key in record:
            return _utc(record.get(key))
    return None


def _float(record: Mapping[str, Any], key: str) -> float | None:
    try:
        return float(record.get(key))
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class TimeframeCertification:
    timeframe: str
    status: str
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    out_of_order_records: int
    gap_count: int
    estimated_missing_records: int
    first_timestamp_utc: str
    last_timestamp_utc: str
    coverage_days: float
    invalid_ratio: float
    duplicate_ratio: float
    missing_ratio: float
    quality_score: float
    research_eligible: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        return payload


@dataclass(frozen=True)
class DatasetCertificationReport:
    schema_version: str
    dataset_id: str
    instrument: str
    source_id: str
    generated_at_utc: str
    overall_status: str
    research_eligible: bool
    required_timeframes: tuple[str, ...]
    ready_timeframes: tuple[str, ...]
    caution_timeframes: tuple[str, ...]
    quarantined_timeframes: tuple[str, ...]
    timeframe_results: tuple[TimeframeCertification, ...]
    policy: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_timeframes"] = list(self.required_timeframes)
        payload["ready_timeframes"] = list(self.ready_timeframes)
        payload["caution_timeframes"] = list(self.caution_timeframes)
        payload["quarantined_timeframes"] = list(self.quarantined_timeframes)
        payload["timeframe_results"] = [item.to_dict() for item in self.timeframe_results]
        return payload


class HistoricalDatasetCertifier:
    """Deterministically certify closed OHLC data for historical research."""

    def __init__(self, policy: Mapping[str, Any] | None = None) -> None:
        defaults = {
            "required_timeframes": list(REQUIRED_TIMEFRAMES),
            "minimum_valid_records": 100,
            "minimum_coverage_days": 1.0,
            "maximum_invalid_ratio_ready": 0.0,
            "maximum_duplicate_ratio_ready": 0.0,
            "maximum_missing_ratio_ready": 0.02,
            "maximum_invalid_ratio_caution": 0.01,
            "maximum_duplicate_ratio_caution": 0.01,
            "maximum_missing_ratio_caution": 0.10,
            "quarantine_on_non_positive_price": True,
        }
        defaults.update(dict(policy or {}))
        self.policy = defaults

    @classmethod
    def from_policy_file(cls, path: str | Path) -> "HistoricalDatasetCertifier":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def certify(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        instrument: str,
        source_id: str,
        generated_at_utc: datetime | None = None,
    ) -> DatasetCertificationReport:
        grouped: dict[str, list[Mapping[str, Any]]] = {tf: [] for tf in self.policy["required_timeframes"]}
        stable_rows: list[dict[str, Any]] = []
        for record in records:
            row = dict(record)
            tf = str(row.get("timeframe", "")).strip().upper()
            if tf in grouped:
                grouped[tf].append(row)
                stable_rows.append(row)

        results = tuple(self._certify_timeframe(tf, grouped[tf]) for tf in self.policy["required_timeframes"])
        ready = tuple(item.timeframe for item in results if item.status == "READY")
        caution = tuple(item.timeframe for item in results if item.status == "CAUTION")
        quarantined = tuple(item.timeframe for item in results if item.status == "QUARANTINED")
        if quarantined:
            overall = "QUARANTINED"
        elif caution:
            overall = "CAUTION"
        else:
            overall = "READY"
        canonical = json.dumps(stable_rows, sort_keys=True, separators=(",", ":"), default=str)
        dataset_id = sha256((instrument + "|" + source_id + "|" + canonical).encode("utf-8")).hexdigest()
        now = (generated_at_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
        return DatasetCertificationReport(
            schema_version="historical-dataset-certification.v1",
            dataset_id=dataset_id,
            instrument=str(instrument),
            source_id=str(source_id),
            generated_at_utc=now.isoformat().replace("+00:00", "Z"),
            overall_status=overall,
            research_eligible=overall != "QUARANTINED" and all(item.research_eligible for item in results),
            required_timeframes=tuple(self.policy["required_timeframes"]),
            ready_timeframes=ready,
            caution_timeframes=caution,
            quarantined_timeframes=quarantined,
            timeframe_results=results,
            policy=dict(self.policy),
        )

    def _certify_timeframe(self, timeframe: str, rows: Sequence[Mapping[str, Any]]) -> TimeframeCertification:
        expected = TIMEFRAME_SECONDS[timeframe]
        total = len(rows)
        valid: list[datetime] = []
        invalid = 0
        non_positive = False
        out_of_order = 0
        previous_input: datetime | None = None
        for row in rows:
            ts = _timestamp(row)
            o, h, l, c = (_float(row, key) for key in ("open", "high", "low", "close"))
            good = ts is not None and None not in (o, h, l, c)
            if good:
                assert o is not None and h is not None and l is not None and c is not None
                if min(o, h, l, c) <= 0:
                    non_positive = True
                    good = False
                elif h < max(o, c) or l > min(o, c) or h < l:
                    good = False
            if not good:
                invalid += 1
                continue
            assert ts is not None
            if previous_input is not None and ts < previous_input:
                out_of_order += 1
            previous_input = ts
            valid.append(ts)

        valid.sort()
        duplicates = len(valid) - len(set(valid))
        unique = sorted(set(valid))
        gaps = 0
        missing = 0
        for left, right in zip(unique, unique[1:]):
            delta = int((right - left).total_seconds())
            if delta > expected:
                estimated = max(0, delta // expected - 1)
                if estimated:
                    gaps += 1
                    missing += estimated
        first = unique[0] if unique else None
        last = unique[-1] if unique else None
        coverage_days = ((last - first).total_seconds() / 86400.0) if first and last else 0.0
        valid_count = len(unique)
        invalid_ratio = invalid / total if total else 1.0
        duplicate_ratio = duplicates / total if total else 0.0
        denominator = valid_count + missing
        missing_ratio = missing / denominator if denominator else 1.0
        reasons: list[str] = []

        if total == 0:
            status = "QUARANTINED"; reasons.append("NO_DATA")
        elif non_positive and self.policy["quarantine_on_non_positive_price"]:
            status = "QUARANTINED"; reasons.append("NON_POSITIVE_PRICE")
        elif valid_count < int(self.policy["minimum_valid_records"]):
            status = "QUARANTINED"; reasons.append("INSUFFICIENT_VALID_RECORDS")
        elif coverage_days < float(self.policy["minimum_coverage_days"]):
            status = "QUARANTINED"; reasons.append("INSUFFICIENT_COVERAGE")
        elif (invalid_ratio > float(self.policy["maximum_invalid_ratio_caution"]) or
              duplicate_ratio > float(self.policy["maximum_duplicate_ratio_caution"]) or
              missing_ratio > float(self.policy["maximum_missing_ratio_caution"])):
            status = "QUARANTINED"; reasons.append("QUALITY_LIMIT_EXCEEDED")
        elif (invalid_ratio > float(self.policy["maximum_invalid_ratio_ready"]) or
              duplicate_ratio > float(self.policy["maximum_duplicate_ratio_ready"]) or
              missing_ratio > float(self.policy["maximum_missing_ratio_ready"]) or out_of_order):
            status = "CAUTION"; reasons.append("QUALITY_REVIEW_REQUIRED")
        else:
            status = "READY"; reasons.append("QUALITY_REQUIREMENTS_MET")

        score = max(0.0, 100.0 * (1.0 - min(1.0, invalid_ratio + duplicate_ratio + missing_ratio)))
        if out_of_order:
            score = max(0.0, score - min(20.0, out_of_order * 0.1))
        return TimeframeCertification(
            timeframe=timeframe, status=status, total_records=total, valid_records=valid_count,
            invalid_records=invalid, duplicate_records=duplicates, out_of_order_records=out_of_order,
            gap_count=gaps, estimated_missing_records=missing,
            first_timestamp_utc=first.isoformat().replace("+00:00", "Z") if first else "",
            last_timestamp_utc=last.isoformat().replace("+00:00", "Z") if last else "",
            coverage_days=round(coverage_days, 6), invalid_ratio=round(invalid_ratio, 8),
            duplicate_ratio=round(duplicate_ratio, 8), missing_ratio=round(missing_ratio, 8),
            quality_score=round(score, 4), research_eligible=status in {"READY", "CAUTION"},
            reasons=tuple(reasons),
        )


def write_report(report: DatasetCertificationReport, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
