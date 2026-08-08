"""Deterministic timeframe coverage, gap, freshness, and backfill evidence.

Research-only utilities.  This module has no order execution authority and does
not change live trading policy.  It analyses closed OHLC bars and can merge
provider-supplied backfill records without mutating existing records.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
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
    classification: str = "UNEXPECTED_DATA_GAP"
    expected_closure_bar_count: int = 0
    unexpected_missing_bar_count: int = 0
    backfill_eligible: bool = True
    reason_codes: tuple[str, ...] = ()

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
    expected_closure_gap_count: int = 0
    expected_closure_bars: int = 0
    unexpected_gap_count: int = 0
    unexpected_missing_bars: int = 0

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

    def __init__(
        self,
        *,
        freshness_multiplier: int = 3,
        expected_closure_dates: Iterable[str | date] = (),
        daily_session_closure_utc: tuple[str, str] | None = None,
        daily_session_closure_timeframes: Iterable[str] = (),
    ) -> None:
        self.freshness_multiplier = max(1, int(freshness_multiplier))
        closure_dates: set[date] = set()
        for value in expected_closure_dates:
            if isinstance(value, date):
                closure_dates.add(value)
                continue
            try:
                closure_dates.add(date.fromisoformat(str(value)))
            except ValueError as exc:
                raise ValueError(f"invalid expected closure date: {value!r}") from exc
        self.expected_closure_dates = frozenset(closure_dates)
        self.daily_session_closure_utc = self._parse_daily_closure(daily_session_closure_utc)
        self.daily_session_closure_timeframes = frozenset(
            str(value).strip().upper() for value in daily_session_closure_timeframes if str(value).strip()
        )

    @staticmethod
    def _parse_daily_closure(value: tuple[str, str] | None) -> tuple[time, time] | None:
        if value is None:
            return None
        if len(value) != 2:
            raise ValueError("daily_session_closure_utc requires (start_utc, end_utc)")
        try:
            start = time.fromisoformat(str(value[0]))
            end = time.fromisoformat(str(value[1]))
        except ValueError as exc:
            raise ValueError("daily_session_closure_utc must use HH:MM or HH:MM:SS") from exc
        if start == end:
            raise ValueError("daily_session_closure_utc start and end must differ")
        return start, end

    def _within_daily_session_closure(self, timestamp: datetime, timeframe: str) -> bool:
        window = self.daily_session_closure_utc
        if window is None or timeframe not in self.daily_session_closure_timeframes:
            return False
        start, end = window
        current = timestamp.timetz().replace(tzinfo=None)
        return start <= current < end if start < end else current >= start or current < end

    def _expected_market_closure(
        self,
        timestamp: datetime,
        *,
        timeframe: str,
        weekend_closure_allowed: bool,
    ) -> tuple[bool, str | None]:
        if self._within_daily_session_closure(timestamp, timeframe):
            return True, "CONFIGURED_DAILY_SESSION_CLOSURE"
        if weekend_closure_allowed and timestamp.weekday() in {5, 6}:
            return True, "WEEKEND_MARKET_CLOSURE"
        if timestamp.date() in self.expected_closure_dates:
            return True, "CONFIGURED_MARKET_CLOSURE"
        return False, None

    def _classify_gap(
        self,
        timeframe: str,
        left: datetime,
        right: datetime,
        expected: int,
        observed: int,
    ) -> GapRange:
        expected_closures = 0
        unexpected = 0
        reasons: set[str] = set()
        # Weekend classification requires a real boundary from a weekday close
        # into a later reopening day. Synthetic/intraday data already present
        # inside a weekend remains subject to ordinary continuity checks.
        weekend_closure_allowed = (
            left.date() < right.date()
            and right.weekday() != 5
            # A D1 feed can legitimately include a Saturday settlement bar.
            # Sunday remains a known market closure in that representation.
            # Intraday feeds retain the stricter synthetic-weekend safeguard.
            and (timeframe == "D1" or left.weekday() not in {5, 6})
        )
        candidate = left + timedelta(seconds=expected)
        while candidate < right:
            is_expected, reason = self._expected_market_closure(
                candidate,
                timeframe=timeframe,
                weekend_closure_allowed=weekend_closure_allowed,
            )
            if is_expected:
                expected_closures += 1
                if reason:
                    reasons.add(reason)
            else:
                unexpected += 1
            candidate += timedelta(seconds=expected)
        if unexpected == 0:
            classification = "EXPECTED_MARKET_CLOSURE"
        elif expected_closures == 0:
            classification = "UNEXPECTED_DATA_GAP"
            reasons.add("UNSCHEDULED_INTERVAL_MISSING")
        else:
            classification = "MIXED_MARKET_CLOSURE_AND_DATA_GAP"
            reasons.add("UNSCHEDULED_INTERVAL_MISSING")
        return GapRange(
            timeframe=timeframe,
            after_timestamp_utc=left.isoformat().replace("+00:00", "Z"),
            before_timestamp_utc=right.isoformat().replace("+00:00", "Z"),
            missing_bar_count=expected_closures + unexpected,
            expected_interval_seconds=expected,
            observed_interval_seconds=observed,
            classification=classification,
            expected_closure_bar_count=expected_closures,
            unexpected_missing_bar_count=unexpected,
            backfill_eligible=unexpected > 0,
            reason_codes=tuple(sorted(reasons)),
        )

    @staticmethod
    def _valid_bar(record: Mapping[str, Any], timeframe: str) -> tuple[datetime, dict[str, Any]] | None:
        if str(record.get("timeframe", "")).strip().upper() != timeframe:
            return None
        timestamp = _parse_utc(record.get("timestamp_utc"))
        if timestamp is None:
            return None
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
                    gaps.append(self._classify_gap(timeframe, left, right, expected, observed))
            first = unique[0][0] if unique else None
            last = unique[-1][0] if unique else None
            age = max(0, int((now - last).total_seconds())) if last else None
            freshness_limit = expected * self.freshness_multiplier
            fresh = age <= freshness_limit if age is not None else None
            missing_total = sum(item.missing_bar_count for item in gaps)
            expected_closure_bars = sum(item.expected_closure_bar_count for item in gaps)
            unexpected_missing_bars = sum(item.unexpected_missing_bar_count for item in gaps)
            expected_closure_gap_count = sum(item.classification == "EXPECTED_MARKET_CLOSURE" for item in gaps)
            unexpected_gap_count = sum(item.unexpected_missing_bar_count > 0 for item in gaps)
            if not unique:
                status = "NO_DATA"
            elif invalid or duplicates or unexpected_gap_count:
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
                expected_closure_gap_count=expected_closure_gap_count,
                expected_closure_bars=expected_closure_bars,
                unexpected_gap_count=unexpected_gap_count,
                unexpected_missing_bars=unexpected_missing_bars,
            )
        return result

    def research_segments(
        self,
        bars: Sequence[Mapping[str, Any]],
        evidence: TimeframeQualityEvidence,
    ) -> tuple[tuple[dict[str, Any], ...], ...]:
        """Partition valid bars only at unresolved unexpected-gap boundaries.

        Expected market closures remain within one chronological research
        segment.  An unresolved gap starts a new segment so rolling features
        cannot silently bridge missing market evidence.
        """
        normalized: list[tuple[datetime, dict[str, Any]]] = []
        seen: set[str] = set()
        for record in bars:
            item = self._valid_bar(record, evidence.timeframe)
            if item is None:
                continue
            timestamp, value = item
            if value["timestamp_utc"] in seen:
                continue
            seen.add(value["timestamp_utc"])
            normalized.append((timestamp, value))
        normalized.sort(key=lambda item: item[0])
        boundaries = {
            (gap.after_timestamp_utc, gap.before_timestamp_utc)
            for gap in evidence.gaps
            if gap.unexpected_missing_bar_count > 0
        }
        segments: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        previous_timestamp = ""
        for _, value in normalized:
            timestamp = str(value["timestamp_utc"])
            if current and (previous_timestamp, timestamp) in boundaries:
                segments.append(current)
                current = []
            current.append(value)
            previous_timestamp = timestamp
        if current:
            segments.append(current)
        return tuple(tuple(segment) for segment in segments)

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
                if not gap.backfill_eligible:
                    continue
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
