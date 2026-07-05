from .base import AnalyzerResult

class EntryAnalyzer:
    def evaluate(self, context=None):
        return AnalyzerResult(
            score=0.0,
            recommendation="WAIT",
            details={"analyzer":"EntryAnalyzer"}
        )
