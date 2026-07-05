class TradeAnalytics:
    def summarize(self, trades: list) -> dict:
        total = len(trades)
        wins = sum(1 for t in trades if float(t.get("profit", 0)) > 0)
        losses = sum(1 for t in trades if float(t.get("profit", 0)) < 0)
        net_profit = sum(float(t.get("profit", 0)) for t in trades)

        win_rate = (wins / total * 100) if total else 0.0
        avg_profit = (net_profit / total) if total else 0.0

        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "net_profit": round(net_profit, 2),
            "avg_profit": round(avg_profit, 2),
        }
