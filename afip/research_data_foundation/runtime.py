"""Machine-readable AFIP research-data contracts.

This module is deliberately side-effect free. It validates dictionaries and builds
trace/eligibility envelopes, but it never sends orders and never mutates raw data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping


class RegistryValidationError(ValueError):
    """Raised when a machine-readable research registry is incomplete or invalid."""


@dataclass(frozen=True)
class ResearchEligibility:
    eligible: bool
    classification: str
    reasons: tuple[str, ...]
    rule_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "classification": self.classification,
            "reasons": list(self.reasons),
            "rule_version": self.rule_version,
        }


@dataclass(frozen=True)
class DecisionTraceEnvelope:
    trace_id: str
    observed_at_utc: str
    formula_version: str
    data_dictionary_version: str
    score_dictionary_version: str
    market_context: Mapping[str, Any]
    score_components: Mapping[str, Any]
    gates: Mapping[str, Any]
    decision: Mapping[str, Any]
    research_eligibility: ResearchEligibility
    source_timestamps: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        trace_id: str,
        formula_version: str,
        data_dictionary_version: str,
        score_dictionary_version: str,
        market_context: Mapping[str, Any],
        score_components: Mapping[str, Any],
        gates: Mapping[str, Any],
        decision: Mapping[str, Any],
        research_eligibility: ResearchEligibility,
        source_timestamps: Mapping[str, str] | None = None,
        observed_at_utc: str | None = None,
    ) -> "DecisionTraceEnvelope":
        if not trace_id.strip():
            raise RegistryValidationError("trace_id must not be empty")
        timestamp = observed_at_utc or datetime.now(timezone.utc).isoformat()
        if "+00:00" not in timestamp and not timestamp.endswith("Z"):
            raise RegistryValidationError("observed_at_utc must be UTC")
        return cls(
            trace_id=trace_id,
            observed_at_utc=timestamp,
            formula_version=formula_version,
            data_dictionary_version=data_dictionary_version,
            score_dictionary_version=score_dictionary_version,
            market_context=dict(market_context),
            score_components=dict(score_components),
            gates=dict(gates),
            decision=dict(decision),
            research_eligibility=research_eligibility,
            source_timestamps=dict(source_timestamps or {}),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "observed_at_utc": self.observed_at_utc,
            "formula_version": self.formula_version,
            "data_dictionary_version": self.data_dictionary_version,
            "score_dictionary_version": self.score_dictionary_version,
            "market_context": dict(self.market_context),
            "score_components": dict(self.score_components),
            "gates": dict(self.gates),
            "decision": dict(self.decision),
            "research_eligibility": self.research_eligibility.as_dict(),
            "source_timestamps": dict(self.source_timestamps),
        }


class DataFoundationRegistry:
    """Loads and validates AFIP data, score, formula, quality and eligibility registries."""

    REQUIRED_FILES = {
        "data": "data_dictionary.json",
        "score": "score_dictionary.json",
        "formula": "formula_registry.json",
        "quality": "data_quality_rules.json",
        "eligibility": "research_eligibility_rules.json",
    }

    def __init__(self, root: Path):
        self.root = Path(root)
        self.payloads = {
            name: self._load_json(self.root / filename)
            for name, filename in self.REQUIRED_FILES.items()
        }
        self.validate()

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise RegistryValidationError(f"missing registry file: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RegistryValidationError(f"invalid registry file: {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise RegistryValidationError(f"registry root must be an object: {path}")
        return payload

    def validate(self) -> None:
        for name, payload in self.payloads.items():
            if not payload.get("version"):
                raise RegistryValidationError(f"{name} registry requires version")
            if payload.get("immutable_raw_data") is not True:
                raise RegistryValidationError(f"{name} registry must preserve immutable raw data")

        fields = self.payloads["data"].get("fields", [])
        field_ids = [item.get("field_id") for item in fields]
        self._require_unique_nonempty(field_ids, "data field_id")
        for item in fields:
            for key in ("meaning", "data_type", "source", "unit", "quality_rules", "lineage"):
                if key not in item:
                    raise RegistryValidationError(f"data field {item.get('field_id')} missing {key}")

        scores = self.payloads["score"].get("scores", [])
        score_ids = [item.get("score_id") for item in scores]
        self._require_unique_nonempty(score_ids, "score_id")
        for item in scores:
            for key in ("range", "components", "formula_id", "hard_gates", "interpretation"):
                if key not in item:
                    raise RegistryValidationError(f"score {item.get('score_id')} missing {key}")

        formulas = self.payloads["formula"].get("formulas", [])
        formula_ids = [item.get("formula_id") for item in formulas]
        self._require_unique_nonempty(formula_ids, "formula_id")
        known = set(formula_ids)
        for score in scores:
            if score["formula_id"] not in known:
                raise RegistryValidationError(
                    f"score {score['score_id']} references unknown formula {score['formula_id']}"
                )

        if not self.payloads["quality"].get("dimensions"):
            raise RegistryValidationError("quality registry requires dimensions")
        if not self.payloads["eligibility"].get("classifications"):
            raise RegistryValidationError("eligibility registry requires classifications")

    @staticmethod
    def _require_unique_nonempty(values: list[Any], label: str) -> None:
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise RegistryValidationError(f"{label} values must be non-empty strings")
        if len(values) != len(set(values)):
            raise RegistryValidationError(f"duplicate {label}")

    @property
    def versions(self) -> dict[str, str]:
        return {name: payload["version"] for name, payload in self.payloads.items()}

    def evaluate_research_eligibility(
        self,
        *,
        data_quality_status: str,
        execution_incident: bool,
        configuration_incident: bool,
        lookahead_detected: bool,
    ) -> ResearchEligibility:
        version = self.payloads["eligibility"]["version"]
        reasons: list[str] = []
        if lookahead_detected:
            reasons.append("lookahead_detected")
        if execution_incident:
            reasons.append("execution_incident")
        if configuration_incident:
            reasons.append("configuration_incident")
        if data_quality_status not in {"PASS", "CAUTION"}:
            reasons.append("data_quality_not_acceptable")
        eligible = not reasons
        classification = "RESEARCH_ELIGIBLE" if eligible else "QUARANTINED"
        return ResearchEligibility(eligible, classification, tuple(reasons), version)
