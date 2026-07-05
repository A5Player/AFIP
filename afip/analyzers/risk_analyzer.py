from .base import AnalyzerResult

class RiskAnalyzer:
    def evaluate(self, context=None):
        return AnalyzerResult(
            score=0.0,
            recommendation="WAIT",
            details={"analyzer":"RiskAnalyzer"}
        )
