"""Read-only portfolio and multi-profile authority certification for AFIP V1."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
PROFILES = ("P1", "P2", "P3", "P4")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def _float(value: Any) -> float | None:
    try:
        if value in (None, "", DATA_UNAVAILABLE):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_or_unavailable(values: list[float | None]) -> float | str:
    return round(sum(v for v in values if v is not None), 2) if values and all(v is not None for v in values) else DATA_UNAVAILABLE


class PortfolioMultiProfileAuthorityRuntime:
    """Aggregate verified P1-P4 financial and exposure evidence without affecting trading."""

    def __init__(self, project_root: str | Path = "."):
        self.root = Path(project_root)

    def _financial(self) -> dict[str, Any]:
        path = self.root / "runtime" / "certification" / "financial_integrity.json"
        return _load(path)

    def _profile_exposure(self, profile_id: str) -> dict[str, Any]:
        base = self.root / "runtime" / "profiles" / profile_id.lower()
        for name in ("portfolio_exposure.json", "position_exposure.json", "demo_execution_state.json", "status.json"):
            path = base / name
            data = _load(path)
            if data:
                open_positions = data.get("open_positions", data.get("positions", []))
                if not isinstance(open_positions, list):
                    open_positions = []
                buy_lots = sell_lots = risk_usd = floating_usd = 0.0
                known_risk = known_float = True
                for row in open_positions:
                    if not isinstance(row, Mapping):
                        continue
                    side = str(row.get("direction", row.get("type", ""))).upper()
                    lot = _float(row.get("volume", row.get("lot", row.get("lots")))) or 0.0
                    if side == "BUY": buy_lots += lot
                    elif side == "SELL": sell_lots += lot
                    risk = _float(row.get("remaining_risk_usd", row.get("risk_usd")))
                    pnl = _float(row.get("profit", row.get("unrealized_profit_usd", row.get("floating_usd"))))
                    if risk is None: known_risk = False
                    else: risk_usd += risk
                    if pnl is None: known_float = False
                    else: floating_usd += pnl
                return {
                    "source": str(path.relative_to(self.root)),
                    "open_position_count": len(open_positions),
                    "buy_lots": round(buy_lots, 4),
                    "sell_lots": round(sell_lots, 4),
                    "net_lots": round(buy_lots - sell_lots, 4),
                    "remaining_risk_usd": round(risk_usd, 2) if known_risk else DATA_UNAVAILABLE,
                    "floating_profit_usd": round(floating_usd, 2) if known_float else DATA_UNAVAILABLE,
                }
        return {"source": DATA_UNAVAILABLE, "open_position_count": DATA_UNAVAILABLE, "buy_lots": DATA_UNAVAILABLE, "sell_lots": DATA_UNAVAILABLE, "net_lots": DATA_UNAVAILABLE, "remaining_risk_usd": DATA_UNAVAILABLE, "floating_profit_usd": DATA_UNAVAILABLE}

    def evaluate(self) -> dict[str, Any]:
        financial = self._financial()
        rows_by_id = {str(row.get("profile_id", "")).upper(): row for row in financial.get("profiles", []) if isinstance(row, Mapping)}
        profiles = []
        currencies = set()
        for profile_id in PROFILES:
            fin = dict(rows_by_id.get(profile_id, {}))
            exposure = self._profile_exposure(profile_id)
            currency = fin.get("currency", DATA_UNAVAILABLE)
            if currency != DATA_UNAVAILABLE: currencies.add(str(currency))
            verified = fin.get("status") == "VERIFIED"
            profiles.append({
                "profile_id": profile_id,
                "financial_status": fin.get("status", DATA_UNAVAILABLE),
                "currency": currency,
                "balance": fin.get("balance", DATA_UNAVAILABLE),
                "equity": fin.get("equity", DATA_UNAVAILABLE),
                "margin": fin.get("margin", DATA_UNAVAILABLE),
                "free_margin": fin.get("free_margin", DATA_UNAVAILABLE),
                "available_allocation": fin.get("available_allocation", DATA_UNAVAILABLE),
                "data_freshness": fin.get("data_freshness", "UNKNOWN"),
                "exposure": exposure,
                "profile_authority_status": "VERIFIED" if verified else DATA_UNAVAILABLE,
            })
        all_verified = all(row["profile_authority_status"] == "VERIFIED" for row in profiles)
        currency_consistent = len(currencies) == 1 and all_verified
        totals = {}
        for key in ("balance", "equity", "margin", "free_margin", "available_allocation"):
            totals[key] = _sum_or_unavailable([_float(row.get(key)) for row in profiles])
        exposure_totals = {
            "open_position_count": _sum_or_unavailable([_float(row["exposure"].get("open_position_count")) for row in profiles]),
            "buy_lots": _sum_or_unavailable([_float(row["exposure"].get("buy_lots")) for row in profiles]),
            "sell_lots": _sum_or_unavailable([_float(row["exposure"].get("sell_lots")) for row in profiles]),
            "net_lots": _sum_or_unavailable([_float(row["exposure"].get("net_lots")) for row in profiles]),
            "remaining_risk_usd": _sum_or_unavailable([_float(row["exposure"].get("remaining_risk_usd")) for row in profiles]),
            "floating_profit_usd": _sum_or_unavailable([_float(row["exposure"].get("floating_profit_usd")) for row in profiles]),
        }
        equity = _float(totals.get("equity")); risk = _float(exposure_totals.get("remaining_risk_usd"))
        risk_pct = round(risk / equity * 100.0, 4) if equity and risk is not None else DATA_UNAVAILABLE
        blockers = []
        if not all_verified: blockers.append("profile_financial_authority_incomplete")
        if not currency_consistent: blockers.append("portfolio_currency_inconsistent_or_unavailable")
        if exposure_totals["remaining_risk_usd"] == DATA_UNAVAILABLE: blockers.append("portfolio_risk_usd_unavailable")
        status = "VERIFIED" if not blockers else "REVIEW_REQUIRED"
        return {
            "schema_version": "afip_v1_portfolio_multi_profile_authority_v1",
            "status": status,
            "profiles": profiles,
            "portfolio_total": {"currency": next(iter(currencies)) if currency_consistent else DATA_UNAVAILABLE, **totals, **exposure_totals, "portfolio_risk_percent_of_equity": risk_pct},
            "currency_consistent": currency_consistent,
            "correlation_status": "DATA_UNAVAILABLE",
            "correlation_reason": "paired_period_return_series_not_certified",
            "authority_blockers": blockers,
            "affects_trading": False,
            "execution_permission": False,
            "automatic_allocation_change_allowed": False,
        }

    def write(self, output: str | Path = "runtime/certification/portfolio_multi_profile_authority.json") -> Path:
        path = self.root / output
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.evaluate(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
