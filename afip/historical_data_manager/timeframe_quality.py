"""Deterministic timeframe coverage, gap, freshness, and backfill evidence.

Research-only utilities.  This module has no order execution authority and does
not change live trading policy.  It analyses closed OHLC bars and can merge
provider-supplied backfill records without mutating existing records.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Sequence

from afip.timeframe_registry import get_seconds, get_supported_timeframes, is_supported


def _parse_utc(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(text)
    except ValueError:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class GapRange:
    timeframe: str
    after_timestamp_utc: str
    before_timestamp_utc: str
    missing_bar_count: int
    expected_interval_seconds: int
    observed_interval_seconds: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimeframeQualityEvidence:
    timeframe: str
    available_bars: int
    valid_bars: int
    invalid_bars: int
    duplicate_bars: int
    first_timestamp_utc: str
    last_timestamp_utc: str
    gap_count: int
    missing_bars: int
    gaps: tuple[GapRange, ...]
    freshness_age_seconds: int | None
    freshness_limit_seconds: int
    fresh: bool | None
    integrity_status: str
    research_eligible: bool

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["gaps"] = [gap.as_dict() for gap in self.gaps]
        return payload


@dataclass(frozen=True)
class BackfillResult:
    requested_ranges: int
    returned_bars: int
    accepted_bars: int
    duplicate_bars: int
    invalid_bars: int
    merged_bars: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("merged_bars", None)
        return payload


class TimeframeDataQuality:
    """Evaluate registered timeframe bars and safely merge backfill output."""

    def __init__(self, *, freshness_multiplier: int = 3) -> None:
        self.freshness_multiplier = max(1, int(freshness_multiplier))

    @staticmethod
    def _valid_bar(record: Mapping[str, Any], timeframe: str) -> tuple[datetime, dict[str, Any]] | None:
        if str(record.get("timeframe", "")).strip().upper() != timeframe:
            return None
        timestamp = _parse_utc(record.get("timestamp_utc"))
        try:
            open_value = float(record.get("open"))
            high_value = float(record.get("high"))
            low_value = float(record.get("low"))
            close_value = float(record.get("close"))
        except (TypeError, ValueError):
            return None
        if high_value < low_value or high_value < max(open_value, close_value) or low_value > min(open_value, close_value):
            return None
        normalized = dict(record)
        normalized.update({
            "timeframe": timeframe,
            "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
            "open": open_value,
            "high": high_value,
            "low": low_value,
            "close": close_value,
        })
        return timestamp, normalized

    def evaluate(
        self,
        bars: Sequence[Mapping[str, Any]],
        *,
        now_utc: datetime | None = None,
    ) -> dict[str, TimeframeQualityEvidence]:
        now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
        result: dict[str, TimeframeQualityEvidence] = {}
        for timeframe in get_supported_timeframes(capability="gap_detection"):
            raw = [record for record in bars if str(record.get("timeframe", "")).strip().upper() == timeframe]
            parsed: list[tuple[datetime, dict[str, Any]]] = []
            invalid = 0
            for record in raw:
                item = self._valid_bar(record, timeframe)
                if item is None:
                    invalid += 1
                else:
                    parsed.append(item)
            parsed.sort(key=lambda item: item[0])
            unique: list[tuple[datetime, dict[str, Any]]] = []
            seen: set[str] = set()
            duplicates = 0
            for timestamp, record in parsed:
                key = record["timestamp_utc"]
                if key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
                unique.append((timestamp, record))
            expected = get_seconds(timeframe)
            gaps: list[GapRange] = []
            for (left, _), (right, _) in zip(unique, unique[1:]):
                observed = int((right - left).total_seconds())
                missing = max(0, (observed // expected) - 1) if observed > expected else 0
                if missing:
                    gaps.append(GapRange(
                        timeframe=timeframe,
                        after_timestamp_utc=left.isoformat().replace("+00:00", "Z"),
                        before_timestamp_utc=right.isoformat().replace("+00:00", "Z"),
                        missing_bar_count=missing,
                        expected_interval_seconds=expected,
                        observed_interval_seconds=observed,
                    ))
            first = unique[0][0] if unique else None
            last = unique[-1][0] if unique else None
            age = max(0, int((now - last).total_seconds())) if last else None
            freshness_limit = expected * self.freshness_multiplier
            fresh = age <= freshness_limit if age is not None else None
            missing_total = sum(item.missing_bar_count for item in gaps)
            if not unique:
                status = "NO_DATA"
            elif invalid or duplicates or gaps:
                status = "REVIEW"
            else:
                status = "PASS"
            result[timeframe] = TimeframeQualityEvidence(
                timeframe=timeframe,
                available_bars=len(raw),
                valid_bars=len(unique),
                invalid_bars=invalid,
                duplicate_bars=duplicates,
                first_timestamp_utc=first.isoformat().replace("+00:00", "Z") if first else "",
                last_timestamp_utc=last.isoformat().replace("+00:00", "Z") if last else "",
                gap_count=len(gaps),
                missing_bars=missing_total,
                gaps=tuple(gaps),
                freshness_age_seconds=age,
                freshness_limit_seconds=freshness_limit,
                fresh=fresh,
                integrity_status=status,
                research_eligible=bool(unique) and invalid == 0,
            )
        return result

    def backfill(
        self,
        bars: Sequence[Mapping[str, Any]],
        evidence: Mapping[str, TimeframeQualityEvidence],
        provider: Callable[[GapRange], Iterable[Mapping[str, Any]]],
    ) -> BackfillResult:
        """Request each detected gap and merge only valid registered bars.

        Existing records win.  The return value is a new deterministic sequence;
        no input file or append-only dataset is rewritten.
        """
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for record in bars:
            timeframe = str(record.get("timeframe", "")).strip().upper()
            timestamp = str(record.get("timestamp_utc", "")).strip()
            if is_supported(timeframe) and timestamp:
                merged[(timeframe, timestamp)] = dict(record)
        requested = returned = accepted = duplicates = invalid = 0
        for timeframe in get_supported_timeframes(capability="gap_detection"):
            item = evidence.get(timeframe)
            if item is None:
                continue
            for gap in item.gaps:
                requested += 1
                for record in provider(gap):
                    returned += 1
                    normalized = self._valid_bar(record, timeframe)
                    if normalized is None:
                        invalid += 1
                        continue
                    _, value = normalized
                    key = (timeframe, value["timestamp_utc"])
                    if key in merged:
                        duplicates += 1
                        continue
                    merged[key] = value
                    accepted += 1
        ordered = tuple(merged[key] for key in sorted(merged))
        return BackfillResult(requested, returned, accepted, duplicates, invalid, ordered)
