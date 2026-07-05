class ExpectancyCalculator:
    def calculate(self, trades: list) -> dict:
        wins = [float(t.get("profit", 0)) for t in trades if float(t.get("profit", 0)) > 0]
        losses = [abs(float(t.get("profit", 0))) for t in trades if float(t.get("profit", 0)) < 0]
        total = len(trades)

        if total == 0:
            return {"expectancy": 0.0, "win_rate": 0.0}

        win_rate = len(wins) / total
        loss_rate = len(losses) / total
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

        return {
            "expectancy": round(expectancy, 2),
            "win_rate": round(win_rate * 100, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
        }
