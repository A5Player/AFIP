"""Portfolio engine for multi-account portfolio readiness."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp


class PortfolioEngine:
    """Aggregate account exposure, drawdown, and active position distribution."""

    name = "PortfolioEngine"

    def evaluate(self, snapshot: dict) -> dict:
        accounts = list(snapshot.get("accounts", []))
        if not accounts:
            return EngineResult(self.name, "LEARNING", "WAIT", 35.0, "portfolio_accounts_not_available", {}).as_dict()
        total_balance = sum(float(account.get("balance", 0.0) or 0.0) for account in accounts)
        total_equity = sum(float(account.get("equity", account.get("balance", 0.0)) or 0.0) for account in accounts)
        open_positions = sum(int(account.get("open_positions", 0) or 0) for account in accounts)
        drawdown_percent = max(0.0, (total_balance - total_equity) / total_balance * 100.0) if total_balance > 0 else 0.0
        active_accounts = sum(1 for account in accounts if int(account.get("open_positions", 0) or 0) > 0)
        concentration_percent = active_accounts / max(1, len(accounts)) * 100.0
        blocked = drawdown_percent >= 12.0 or concentration_percent >= 100.0 and open_positions >= len(accounts) * 2
        action = "WAIT" if blocked else "ALLOW"
        confidence = clamp(90.0 - drawdown_percent * 4.0 - concentration_percent * 0.15)
        return EngineResult(
            self.name,
            "READY" if not blocked else "BLOCKED",
            action,
            confidence,
            "portfolio_ready" if not blocked else "portfolio_risk_concentrated",
            {
                "account_count": len(accounts),
                "active_accounts": active_accounts,
                "open_positions": open_positions,
                "total_balance": round(total_balance, 2),
                "total_equity": round(total_equity, 2),
                "portfolio_drawdown_percent": round(drawdown_percent, 2),
                "concentration_percent": round(concentration_percent, 2),
            },
        ).as_dict()
