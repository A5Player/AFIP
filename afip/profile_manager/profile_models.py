"""Profile Manager models for AFIP Milestone H Pack 3.

A profile is a reusable trading policy. It is not an account, not an MT5
terminal, and not a demo/real label. Account and terminal values are runtime
targets that can be assigned to a profile without permanently binding them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


def _clean(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _clean(value, default).upper()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _int(value: Any, default: int = 0) -> int:
    return int(_float(value, default))


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


@dataclass(frozen=True)
class ProfileDocumentation:
    thai_description: str
    english_description: str
    default_value: str
    recommended_value: str
    example: str
    why: str
    impact: str

    @classmethod
    def build(cls, key: str, default_value: Any, recommended_value: Any, impact: str) -> "ProfileDocumentation":
        readable = key.replace("_", " ").title()
        return cls(
            thai_description=f"คำอธิบายการตั้งค่า {readable} สำหรับแสดงบน Dashboard",
            english_description=f"Dashboard description for {readable} configuration.",
            default_value=str(default_value),
            recommended_value=str(recommended_value),
            example=f"{key}={recommended_value}",
            why="ทำให้ผู้ใช้ตรวจสอบเหตุผลและผลกระทบของค่าก่อนบันทึกได้",
            impact=impact,
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProfileSetting:
    key: str
    value: Any
    documentation: ProfileDocumentation

    def as_dict(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value, "documentation": self.documentation.as_dict()}


@dataclass(frozen=True)
class TradingProfile:
    profile_id: str
    profile_name: str
    profile_type: str
    broker: str
    symbol: str
    account_type: str
    initial_capital: float
    afip_bank_enabled: bool
    capital_per_unit: float
    unit_lot_size: float
    maximum_units: int
    split_orders: bool
    overnight_holding: bool
    risk_level: str
    ai_mode: str
    research_mode: bool
    dashboard_enabled: bool
    notification_enabled: bool
    logging_enabled: bool
    backup_enabled: bool
    documentation: tuple[ProfileSetting, ...]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "TradingProfile":
        profile_name = _clean(raw.get("profile_name", raw.get("name", "Conservative")), "Conservative")
        profile_type = _upper(raw.get("profile_type", profile_name), profile_name.upper())
        maximum_units = max(1, _int(raw.get("maximum_units", raw.get("units", 1)), 1))
        unit_lot_size = 0.01
        capital_per_unit = max(0.0, _float(raw.get("capital_per_unit", 100.0), 100.0))
        fields = {
            "broker": _upper(raw.get("broker", "XM"), "XM"),
            "symbol": _upper(raw.get("symbol", "GOLD#"), "GOLD#"),
            "account_type": _upper(raw.get("account_type", "DEMO"), "DEMO"),
            "initial_capital": max(0.0, _float(raw.get("initial_capital", 100.0), 100.0)),
            "afip_bank_enabled": _bool(raw.get("afip_bank_enabled", True), True),
            "capital_per_unit": capital_per_unit,
            "maximum_units": maximum_units,
            "split_orders": _bool(raw.get("split_orders", True), True),
            "overnight_holding": _bool(raw.get("overnight_holding", False), False),
            "risk_level": _upper(raw.get("risk_level", "CONSERVATIVE"), "CONSERVATIVE"),
            "ai_mode": _upper(raw.get("ai_mode", "EXPLAINABLE"), "EXPLAINABLE"),
            "research_mode": _bool(raw.get("research_mode", profile_type == "RESEARCH"), profile_type == "RESEARCH"),
            "dashboard_enabled": _bool(raw.get("dashboard_enabled", True), True),
            "notification_enabled": _bool(raw.get("notification_enabled", True), True),
            "logging_enabled": _bool(raw.get("logging_enabled", True), True),
            "backup_enabled": _bool(raw.get("backup_enabled", True), True),
        }
        docs = tuple(
            ProfileSetting(key, value, ProfileDocumentation.build(key, value, _recommended_value(key, value), _impact(key)))
            for key, value in fields.items()
        )
        return cls(
            profile_id=_clean(raw.get("profile_id", raw.get("id", profile_name.lower().replace(" ", "_"))), "conservative"),
            profile_name=profile_name,
            profile_type=profile_type,
            unit_lot_size=unit_lot_size,
            documentation=docs,
            **fields,
        )

    @property
    def order_lots(self) -> tuple[float, ...]:
        return tuple(self.unit_lot_size for _ in range(self.maximum_units)) if self.split_orders else (round(self.unit_lot_size * self.maximum_units, 2),)

    @property
    def total_lot_exposure(self) -> float:
        return round(sum(self.order_lots), 2)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["documentation"] = [setting.as_dict() for setting in self.documentation]
        data["order_lots"] = list(self.order_lots)
        data["total_lot_exposure"] = self.total_lot_exposure
        data["profile_is_account"] = False
        data["profile_is_mt5"] = False
        return data


def _recommended_value(key: str, value: Any) -> Any:
    recommendations = {
        "broker": "XM",
        "symbol": "GOLD#",
        "capital_per_unit": "Set from available capital per 0.01 lot unit",
        "maximum_units": "1 for small starting capital, more only after AI approval",
        "split_orders": True,
        "risk_level": "CONSERVATIVE or BALANCED before demo proof",
        "ai_mode": "EXPLAINABLE",
    }
    return recommendations.get(key, value)


def _impact(key: str) -> str:
    impacts = {
        "maximum_units": "Controls approved unit count while preserving 0.01 lot per unit.",
        "capital_per_unit": "Links AFIP Bank capital allocation to each 0.01 lot unit.",
        "overnight_holding": "Controls whether risk can remain open after session close.",
        "research_mode": "Separates research statistics from live statistics.",
    }
    return impacts.get(key, "Affects dashboard validation and profile readiness without changing trading logic.")
