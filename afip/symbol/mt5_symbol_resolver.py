"""
AFIP MT5 symbol resolver.

Purpose:
- Resolve the broker-specific tradable symbol before reading MT5 data.
- Prefer XM GOLD# when available.
- Stay read-only and safe for production preparation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class SymbolResolution:
    requested: str
    resolved: str
    selected: bool
    reason: str
    candidates: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "requested": self.requested,
            "resolved": self.resolved,
            "selected": self.selected,
            "reason": self.reason,
            "candidates": list(self.candidates),
        }


class MT5SymbolResolver:
    """Broker-safe resolver for gold symbols such as GOLD#, GOLD, XAUUSD# and XAUUSD."""

    GOLD_PRIORITY = ("GOLD#", "GOLD", "XAUUSD#", "XAUUSD", "XAUUSDm", "GOLDm")

    def __init__(self, adapter: Any, preferred_symbol: str = "GOLD#"):
        self.adapter = adapter
        self.preferred_symbol = preferred_symbol

    def resolve(self, requested_symbol: str | None = None) -> dict:
        requested = requested_symbol or self.preferred_symbol
        candidates = self._candidate_list(requested)

        if not self._adapter_available():
            return SymbolResolution(
                requested=requested,
                resolved=requested,
                selected=False,
                reason="mt5_adapter_unavailable_keep_requested_symbol",
                candidates=tuple(candidates),
            ).to_dict()

        broker_symbols = self._read_broker_symbols()
        if broker_symbols:
            candidates = self._merge_candidates(candidates, broker_symbols)

        for symbol in candidates:
            selected = self._try_select(symbol)
            if selected:
                return SymbolResolution(
                    requested=requested,
                    resolved=symbol,
                    selected=True,
                    reason="symbol_resolved_and_selected",
                    candidates=tuple(candidates),
                ).to_dict()

        return SymbolResolution(
            requested=requested,
            resolved=requested,
            selected=False,
            reason="no_candidate_symbol_selected",
            candidates=tuple(candidates),
        ).to_dict()

    def _adapter_available(self) -> bool:
        is_available = getattr(self.adapter, "is_available", None)
        return bool(is_available()) if callable(is_available) else False

    def _candidate_list(self, requested: str) -> list[str]:
        base = [requested, self.preferred_symbol, *self.GOLD_PRIORITY]
        return self._dedupe([item for item in base if item])

    def _read_broker_symbols(self) -> list[str]:
        client = getattr(self.adapter, "mt5_client", None)
        symbols_get = getattr(client, "symbols_get", None)
        if symbols_get is None:
            return []
        try:
            symbols = symbols_get()
        except Exception:
            return []
        names = []
        for item in symbols or []:
            name = getattr(item, "name", None)
            if isinstance(item, dict):
                name = item.get("name")
            if name and self._is_gold_like(name):
                names.append(str(name))
        return names

    def _merge_candidates(self, candidates: Iterable[str], broker_symbols: Iterable[str]) -> list[str]:
        scored = []
        for symbol in broker_symbols:
            score = self._symbol_score(symbol)
            scored.append((score, symbol))
        sorted_broker_symbols = [symbol for _, symbol in sorted(scored, key=lambda item: item[0])]
        return self._dedupe([*candidates, *sorted_broker_symbols])

    def _symbol_score(self, symbol: str) -> tuple[int, str]:
        upper = symbol.upper()
        if upper == "GOLD#":
            rank = 0
        elif upper == "GOLD":
            rank = 1
        elif upper.startswith("GOLD"):
            rank = 2
        elif upper == "XAUUSD#":
            rank = 3
        elif upper == "XAUUSD":
            rank = 4
        elif "XAU" in upper or "GOLD" in upper:
            rank = 5
        else:
            rank = 9
        return (rank, upper)

    def _is_gold_like(self, symbol: str) -> bool:
        upper = symbol.upper()
        return "GOLD" in upper or "XAU" in upper

    def _try_select(self, symbol: str) -> bool:
        result = self.adapter.symbol_select(symbol)
        return bool(result.get("selected"))

    @staticmethod
    def _dedupe(values: Iterable[str]) -> list[str]:
        seen = set()
        output = []
        for value in values:
            if value not in seen:
                seen.add(value)
                output.append(value)
        return output
