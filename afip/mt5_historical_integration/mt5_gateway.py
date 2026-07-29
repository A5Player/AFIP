"""Real MetaTrader5 read-only historical gateway for AFIP.

This module never initializes or launches a terminal by path and never calls any
trade function. The operator must open/login to MT5 before running the loader.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping


_TIMEFRAME_NAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")


def _utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class MT5TerminalEvidence:
    status: str
    reason: str
    terminal_connected: bool
    trade_allowed: bool
    company: str | None
    server: str | None
    login_masked: str | None
    terminal_path: str | None
    build: int | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)




@dataclass(frozen=True)
class MT5HistoryDiscoveryEvidence:
    status: str
    reason: str
    symbol: str
    timeframe: str
    earliest_available_utc: str | None
    latest_available_utc: str | None
    bars_observed: int
    probes_completed: int
    terminal_maxbars: int | None
    exhausted_history: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MetaTrader5ReadOnlyGateway:
    """Adapter implementing the ResumableMT5HistoricalProvider gateway contract."""

    def __init__(self, mt5_module: Any | None = None) -> None:
        if mt5_module is None:
            try:
                import MetaTrader5 as mt5_module  # type: ignore
            except ImportError as exc:
                raise RuntimeError("MetaTrader5 Python package is not installed") from exc
        self.mt5 = mt5_module
        self._broker_time_offset_seconds: int | None = None
        self._last_history_discovery: MT5HistoryDiscoveryEvidence | None = None
        self._timeframes = {
            name: getattr(self.mt5, f"TIMEFRAME_{name}") for name in _TIMEFRAME_NAMES
            if hasattr(self.mt5, f"TIMEFRAME_{name}")
        }

    @staticmethod
    def _normal_path(value: str | Path) -> str:
        text = os.path.abspath(os.path.expandvars(str(value))).replace("/", "\\")
        return os.path.normcase(text.rstrip("\\"))

    @classmethod
    def running_terminal_paths(cls) -> set[str]:
        """Return exact running terminal64.exe paths without starting MT5."""
        paths: set[str] = set()
        try:
            import psutil  # type: ignore
            for process in psutil.process_iter(["name", "exe"]):
                try:
                    if str(process.info.get("name") or "").lower() != "terminal64.exe":
                        continue
                    executable = process.info.get("exe")
                    if executable:
                        paths.add(cls._normal_path(executable))
                except Exception:
                    continue
        except Exception:
            pass
        if paths or os.name != "nt":
            return paths
        command = [
            "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
            "$ErrorActionPreference='SilentlyContinue'; "
            "Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\" | "
            "ForEach-Object { $_.ExecutablePath }",
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
            for line in completed.stdout.splitlines():
                line = line.strip()
                if line:
                    paths.add(cls._normal_path(line))
        except Exception:
            pass
        return paths

    def bind_running_terminal(self, terminal_path: str | Path, portable: bool = True) -> tuple[bool, str]:
        """Bind Python MT5 API only after exact process-path proof. Never auto-start MT5."""
        target = Path(terminal_path)
        if not target.is_file():
            return False, "configured_terminal_not_found"
        normalized = self._normal_path(target)
        if normalized not in self.running_terminal_paths():
            return False, "configured_terminal_process_not_running"
        try:
            self.mt5.shutdown()
        except Exception:
            pass
        initialized = bool(self.mt5.initialize(path=str(target), portable=bool(portable)))
        if not initialized:
            error = self.mt5.last_error() if hasattr(self.mt5, "last_error") else None
            return False, f"mt5_initialize_failed:{error}"
        return True, "bound_to_existing_terminal"

    def close(self) -> None:
        try:
            self.mt5.shutdown()
        except Exception:
            pass

    def terminal_evidence(self) -> MT5TerminalEvidence:
        terminal = self.mt5.terminal_info()
        account = self.mt5.account_info()
        if terminal is None or account is None:
            return MT5TerminalEvidence("BLOCKED", "mt5_terminal_or_account_unavailable", False, False,
                                       None, None, None, None, None)
        login = str(getattr(account, "login", ""))
        masked = ("*" * max(0, len(login) - 4) + login[-4:]) if login else None
        connected = bool(getattr(terminal, "connected", True))
        return MT5TerminalEvidence(
            "READY" if connected else "BLOCKED",
            "connected_read_only_history_available" if connected else "terminal_not_connected",
            connected,
            bool(getattr(terminal, "trade_allowed", False)),
            str(getattr(account, "company", "") or "") or None,
            str(getattr(account, "server", "") or "") or None,
            masked,
            str(getattr(terminal, "path", "") or "") or None,
            int(getattr(terminal, "build", 0) or 0) or None,
        )

    def available_symbols(self) -> Iterable[str]:
        values = self.mt5.symbols_get()
        if values is None:
            return ()
        return tuple(str(getattr(item, "name", "")) for item in values if getattr(item, "name", None))

    def _tf(self, timeframe: str) -> Any:
        key = str(timeframe).upper().strip()
        if key not in self._timeframes:
            raise ValueError(f"Unsupported MT5 timeframe: {timeframe}")
        return self._timeframes[key]

    def _now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    @property
    def broker_time_offset_seconds(self) -> int:
        return int(self._broker_time_offset_seconds or 0)

    def _ensure_symbol(self, symbol: str) -> None:
        selector = getattr(self.mt5, "symbol_select", None)
        if callable(selector):
            try:
                selector(symbol, True)
            except Exception:
                pass

    def _detect_broker_time_offset(self, symbol: str, timeframe: str) -> int:
        if self._broker_time_offset_seconds is not None:
            return self._broker_time_offset_seconds
        self._ensure_symbol(symbol)
        rows = self.mt5.copy_rates_from_pos(symbol, self._tf(timeframe), 0, 2)
        if rows is None or len(rows) == 0:
            self._broker_time_offset_seconds = 0
            return 0
        raw_latest = datetime.fromtimestamp(max(int(row["time"]) for row in rows), tz=timezone.utc)
        delta = (raw_latest - self._now_utc()).total_seconds()
        rounded_hours = int(round(delta / 3600.0))
        candidate = rounded_hours * 3600
        # Normalize only plausible whole-hour broker-server offsets. Small drift is normal.
        if abs(rounded_hours) <= 14 and abs(delta - candidate) <= 15 * 60 and abs(candidate) >= 30 * 60:
            self._broker_time_offset_seconds = candidate
        else:
            self._broker_time_offset_seconds = 0
        return self._broker_time_offset_seconds

    def _normalized_timestamp(self, raw_epoch: int, symbol: str, timeframe: str) -> datetime:
        offset = self._detect_broker_time_offset(symbol, timeframe)
        return datetime.fromtimestamp(int(raw_epoch) - offset, tz=timezone.utc)

    @property
    def last_history_discovery(self) -> dict[str, Any] | None:
        return self._last_history_discovery.as_dict() if self._last_history_discovery else None

    def discover_history(self, symbol: str, timeframe: str, *, block_size: int = 10000,
                         maximum_probes: int = 200) -> MT5HistoryDiscoveryEvidence:
        """Discover loaded broker history by walking MT5 bar positions backwards.

        Range-based discovery is circular because it needs a known start date.  Position
        discovery starts at the current bar and advances into older history until MT5
        reports no additional bars or the oldest timestamp stops moving.  Requests are
        intentionally bounded to avoid the all-or-nothing behavior seen with very large
        copy_rates_from_pos counts on some terminals.
        """
        self._ensure_symbol(symbol)
        terminal = self.mt5.terminal_info() if hasattr(self.mt5, "terminal_info") else None
        configured_max = int(getattr(terminal, "maxbars", 0) or 0) or None
        size = max(128, min(int(block_size), 50000))
        max_probes = max(1, min(int(maximum_probes), 1000))

        seen: set[int] = set()
        oldest_raw: int | None = None
        latest_raw: int | None = None
        start_pos = 0
        probes = 0
        exhausted = False
        reason = "history_not_returned"

        while probes < max_probes:
            rows = self.mt5.copy_rates_from_pos(symbol, self._tf(timeframe), start_pos, size)
            probes += 1
            if rows is None or len(rows) == 0:
                exhausted = bool(seen)
                reason = "history_boundary_reached" if seen else "history_not_returned"
                break

            times = [int(row["time"]) for row in rows]
            before = len(seen)
            seen.update(times)
            block_oldest = min(times)
            block_latest = max(times)
            previous_oldest = oldest_raw
            oldest_raw = block_oldest if oldest_raw is None else min(oldest_raw, block_oldest)
            latest_raw = block_latest if latest_raw is None else max(latest_raw, block_latest)

            # No new timestamp or no movement into older history means MT5 reached its boundary.
            if len(seen) == before or (previous_oldest is not None and oldest_raw >= previous_oldest):
                exhausted = True
                reason = "history_boundary_reached"
                break

            returned = len(rows)
            start_pos += returned
            if returned < size:
                exhausted = True
                reason = "history_boundary_reached"
                break
            reason = "maximum_probe_limit_reached"

        if oldest_raw is None or latest_raw is None:
            evidence = MT5HistoryDiscoveryEvidence(
                "NO_DATA", reason, symbol, timeframe, None, None, 0, probes, configured_max, exhausted
            )
        else:
            evidence = MT5HistoryDiscoveryEvidence(
                "READY", reason, symbol, timeframe,
                _utc(self._normalized_timestamp(oldest_raw, symbol, timeframe)),
                _utc(self._normalized_timestamp(latest_raw, symbol, timeframe)),
                len(seen), probes, configured_max, exhausted,
            )
        self._last_history_discovery = evidence
        return evidence

    def earliest_available(self, symbol: str, timeframe: str) -> str | None:
        return self.discover_history(symbol, timeframe).earliest_available_utc

    def latest_closed_bar(self, symbol: str, timeframe: str) -> str | None:
        self._ensure_symbol(symbol)
        # Position 0 may be the currently-forming bar. Position 1 is the latest closed bar.
        rows = self.mt5.copy_rates_from_pos(symbol, self._tf(timeframe), 1, 1)
        if rows is None or len(rows) == 0:
            return None
        return _utc(self._normalized_timestamp(int(rows[0]["time"]), symbol, timeframe))

    def _fetch_from_positions(self, symbol: str, timeframe: str, start: datetime, end: datetime,
                              maximum_bars: int) -> list[Any]:
        """Fallback collection using the position API proven by history discovery.

        Some MT5 terminals return valid rows from ``copy_rates_from_pos`` while
        ``copy_rates_range`` returns an empty array for the same loaded history.
        Walk the terminal cache in bounded blocks, normalize each epoch, retain
        rows inside the requested UTC interval, and return them oldest-first.
        This is read-only and never changes terminal max-bars settings.
        """
        terminal = self.mt5.terminal_info() if hasattr(self.mt5, "terminal_info") else None
        configured_max = int(getattr(terminal, "maxbars", 0) or 0)
        scan_limit = configured_max if configured_max > 0 else max(int(maximum_bars) * 4, 100000)
        scan_limit = max(1, min(scan_limit, 1000000))
        block_size = max(128, min(10000, scan_limit))
        collected: list[Any] = []
        seen: set[int] = set()
        start_pos = 0

        while start_pos < scan_limit:
            count = min(block_size, scan_limit - start_pos)
            block = self.mt5.copy_rates_from_pos(symbol, self._tf(timeframe), start_pos, count)
            if block is None or len(block) == 0:
                break
            added = 0
            for value in block:
                raw_epoch = int(value["time"])
                if raw_epoch in seen:
                    continue
                seen.add(raw_epoch)
                normalized = self._normalized_timestamp(raw_epoch, symbol, timeframe)
                if start <= normalized <= end:
                    collected.append(value)
                    added += 1
            returned = len(block)
            start_pos += returned
            if returned < count:
                break
            # Position zero is newest. Once this block is entirely older than the
            # requested start, all following blocks will also be older.
            normalized_times = [self._normalized_timestamp(int(v["time"]), symbol, timeframe) for v in block]
            if normalized_times and max(normalized_times) < start:
                break

        collected.sort(key=lambda value: int(value["time"]))
        return collected[:max(1, int(maximum_bars))]

    def fetch(self, symbol: str, timeframe: str, start_utc: str, end_utc: str,
              maximum_bars: int) -> list[dict[str, Any]]:
        self._ensure_symbol(symbol)
        start = _parse(start_utc)
        end = _parse(end_utc)
        limit = max(1, int(maximum_bars))
        offset = self._detect_broker_time_offset(symbol, timeframe)
        # MT5 range requests must use the terminal's timestamp basis.
        request_start = start + timedelta(seconds=offset)
        request_end = end + timedelta(seconds=offset)
        rows = self.mt5.copy_rates_range(symbol, self._tf(timeframe), request_start, request_end)
        # Some MT5 builds expose bar epochs in broker-server time but expect UTC
        # datetime arguments in copy_rates_range. Retry once without the detected
        # offset before declaring the range empty.
        if rows is None or len(rows) == 0:
            rows = self.mt5.copy_rates_range(symbol, self._tf(timeframe), start, end)
        if rows is None or len(rows) == 0:
            rows = self._fetch_from_positions(symbol, timeframe, start, end, limit)
        if rows is None or len(rows) == 0:
            return []
        selected = rows[:limit]
        output: list[dict[str, Any]] = []
        for value in selected:
            ts = self._normalized_timestamp(int(value["time"]), symbol, timeframe)
            output.append({
                "timestamp_utc": _utc(ts),
                "open": float(value["open"]), "high": float(value["high"]),
                "low": float(value["low"]), "close": float(value["close"]),
                "volume": float(value["tick_volume"]),
                "spread": int(value["spread"]),
                "real_volume": float(value["real_volume"]),
            })
        output.sort(key=lambda row: str(row["timestamp_utc"]))
        # Advance by one second to avoid rereading the same bar.
        final_ts = _parse(str(output[-1]["timestamp_utc"]))
        output[-1]["next_start_utc"] = _utc(final_ts + timedelta(seconds=1))
        return output


def write_json_atomic(path: str | Path, payload: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(target)
    return target
