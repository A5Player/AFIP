class ConfidenceCalculator:
    def calculate(self, intelligence: dict):
        return {
            "market_confidence": intelligence.get("confidence", 0),
            "overall_confidence": intelligence.get("confidence", 0)
        }
