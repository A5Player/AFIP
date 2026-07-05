class DecisionManager:
    def decide(self, analyzer_results):
        return {
            "action": "WAIT",
            "confidence": 0.0,
            "source_count": len(analyzer_results)
        }
