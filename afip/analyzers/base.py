class AnalyzerResult:
    def __init__(self, score=0.0, recommendation="WAIT", details=None):
        self.score = score
        self.recommendation = recommendation
        self.details = details or {}
