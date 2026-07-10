"""Deterministic profile customization models for Milestone I Pack 0."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
import re

_ALLOWED_BASES = {"CONSERVATIVE", "BALANCED", "GROWTH", "RESEARCH", "CUSTOM"}
_ALLOWED_RISK = {"CONSERVATIVE", "BALANCED", "GROWTH", "RESEARCH"}


def _text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool): return value
    if value is None: return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _int(value: Any, default: int) -> int:
    try: return int(float(value))
    except (TypeError, ValueError): return default


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "custom_profile"


@dataclass(frozen=True)
class CustomProfile:
    profile_id: str
    profile_name: str
    base_profile: str
    risk_level: str
    maximum_units: int
    capital_per_unit: float
    split_orders: bool
    overnight_holding: bool
    research_mode: bool
    active: bool
    archived: bool
    assigned_account_id: str
    version: int
    updated_at_utc: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, version: int = 1) -> "CustomProfile":
        name = _text(raw.get("profile_name", raw.get("name", "Custom Profile")), "Custom Profile")
        base = _text(raw.get("base_profile", raw.get("profile_type", "CUSTOM")), "CUSTOM").upper()
        if base not in _ALLOWED_BASES: base = "CUSTOM"
        risk = _text(raw.get("risk_level", "BALANCED"), "BALANCED").upper()
        if risk not in _ALLOWED_RISK: risk = "BALANCED"
        try: capital = max(0.0, float(raw.get("capital_per_unit", 100.0)))
        except (TypeError, ValueError): capital = 100.0
        return cls(
            profile_id=_text(raw.get("profile_id", raw.get("id", slugify(name))), slugify(name)),
            profile_name=name,
            base_profile=base,
            risk_level=risk,
            maximum_units=max(1, min(100, _int(raw.get("maximum_units", 1), 1))),
            capital_per_unit=capital,
            split_orders=_bool(raw.get("split_orders", True), True),
            overnight_holding=_bool(raw.get("overnight_holding", False), False),
            research_mode=_bool(raw.get("research_mode", base == "RESEARCH"), base == "RESEARCH"),
            active=_bool(raw.get("active", False), False),
            archived=_bool(raw.get("archived", False), False),
            assigned_account_id=_text(raw.get("assigned_account_id", ""), ""),
            version=max(1, version),
            updated_at_utc=_text(raw.get("updated_at_utc", datetime.now(timezone.utc).isoformat()), datetime.now(timezone.utc).isoformat()),
        )

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.update({"unit_lot_size": 0.01, "profile_is_account": False, "profile_is_mt5": False})
        return data


@dataclass(frozen=True)
class ProfileCustomizationReport:
    status: str
    reason_en: str
    reason_th: str
    profile: CustomProfile
    validation_items: tuple[str, ...]
    expected_next_action_en: str
    expected_next_action_th: str
    live_execution_enabled: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self); data["profile"] = self.profile.as_dict(); return data
