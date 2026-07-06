"""Compact market condition signatures for long-term research storage."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from typing import Mapping


@dataclass(frozen=True)
class MarketSignature:
    """Compact representation of a repeated market condition."""

    signature_id: str
    status: str
    components: Mapping[str, str]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "signature_id": self.signature_id,
            "status": self.status,
            "components": dict(self.components),
            "reason": self.reason,
        }


class MarketSignatureEngine:
    """Create stable signatures so repeated market states can be counted instead of duplicated."""

    def build(self, components: Mapping[str, object] | None = None) -> MarketSignature:
        normalized = {str(key): self._bucket(value) for key, value in sorted((components or {}).items())}
        payload = "|".join(f"{key}={value}" for key, value in normalized.items())
        signature_id = sha1(payload.encode("utf-8")).hexdigest()[:12].upper() if payload else "EMPTY_STATE"
        return MarketSignature(signature_id, "MARKET_SIGNATURE_READY", normalized, "market_signature_compacted")

    @staticmethod
    def _bucket(value: object) -> str:
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            text = str(value).strip().upper().replace(" ", "_")
            return text or "EMPTY"
        if numeric <= -5:
            return "STRONG_DOWN"
        if numeric < -0.25:
            return "DOWN"
        if numeric < 0.25:
            return "FLAT"
        if numeric < 5:
            return "UP"
        return "STRONG_UP"
