"""Decision confidence model for normalized financial decision quality."""

from dataclasses import dataclass

@dataclass(frozen=True)
class DecisionConfidenceResult:
    status: str
    confidence: float
    grade: str
    reason: str

class DecisionConfidenceModel:
    """Combines fusion, context, execution, learning, and memory quality."""

    def calculate(self, fusion_score: float, context_score: float, execution_score: float, learning_score: float = 50.0, memory_score: float = 50.0) -> DecisionConfidenceResult:
        components = [fusion_score, context_score, execution_score, learning_score, memory_score]
        normalized = [max(0.0, min(100.0, float(value))) for value in components]
        confidence = round(
            normalized[0] * 0.30 + normalized[1] * 0.20 + normalized[2] * 0.20 + normalized[3] * 0.15 + normalized[4] * 0.15,
            2,
        )
        if confidence >= 80:
            grade = "HIGH"
        elif confidence >= 60:
            grade = "MODERATE"
        else:
            grade = "LOW"
        status = "DECISION_CONFIDENCE_READY" if confidence >= 60 else "DECISION_CONFIDENCE_REVIEW"
        return DecisionConfidenceResult(status, confidence, grade, f"decision_confidence_{grade.lower()}")
