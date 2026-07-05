"""Intelligence weight matrix for Milestone B financial fusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class IntelligenceWeightMatrixResult:
    """Final category-to-intelligence allocation matrix."""

    status: str
    matrix: dict[str, dict[str, float]]
    total_categories: int
    reason: str


class IntelligenceWeightMatrix:
    """Distribute category weights across available intelligence contributors."""

    def build(
        self,
        category_weights: Mapping[str, float],
        intelligence_map: Mapping[str, list[str]],
    ) -> IntelligenceWeightMatrixResult:
        matrix: dict[str, dict[str, float]] = {}
        for category, category_weight in category_weights.items():
            contributors = list(intelligence_map.get(category, [])) or [f"{category}_INTELLIGENCE"]
            contributor_weight = round(float(category_weight) / len(contributors), 4)
            matrix[str(category).upper()] = {str(name): contributor_weight for name in contributors}
        status = "INTELLIGENCE_WEIGHT_MATRIX_READY" if matrix else "INTELLIGENCE_WEIGHT_MATRIX_REVIEW"
        reason = "category_weight_distribution_ready" if matrix else "missing_category_weights"
        return IntelligenceWeightMatrixResult(status, matrix, len(matrix), reason)
