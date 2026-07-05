import csv

class TradeLogExporter:
    def export_csv(self, trades: list, path: str) -> str:
        fieldnames = ["id", "symbol", "action", "profit", "reason"]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for idx, trade in enumerate(trades, start=1):
                writer.writerow({
                    "id": trade.get("id", idx),
                    "symbol": trade.get("symbol", "XAUUSD"),
                    "action": trade.get("action", "WAIT"),
                    "profit": trade.get("profit", 0),
                    "reason": trade.get("reason", ""),
                })

        return path
