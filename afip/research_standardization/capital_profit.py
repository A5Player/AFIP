"""Cumulative 1,000-pattern standards for one-lot profit care and initial capital.

This module is a component of the existing research-standardization authority.
It owns no runtime loop, MT5 session, order permission, or production promotion.
Only new leakage-free observations beyond the persisted sequence are merged into
the cumulative sufficient statistics at each complete 1,000-pattern milestone.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from typing import Any, Iterable, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset
from .runtime import PatternResearchIdentity, PatternShapeSignature


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def _wilson_low(successes: int, samples: int) -> float:
    if samples <= 0:
        return 0.0
    z = 1.959963984540054
    ratio = successes / samples
    denominator = 1.0 + z * z / samples
    centre = ratio + z * z / (2.0 * samples)
    margin = z * math.sqrt((ratio * (1.0 - ratio) + z * z / (4.0 * samples)) / samples)
    return max(0.0, (centre - margin) / denominator)


def _research_key(identity: PatternResearchIdentity, shape: PatternShapeSignature) -> str:
    return f"{identity.research_key}|{shape.bucket_key}"


@dataclass(frozen=True)
class SingleUnitProfitObservation:
    pattern_id: str
    pattern_sequence: int
    research_identity: PatternResearchIdentity
    shape_signature: PatternShapeSignature
    exit_policy_id: str
    policy_parameters: Mapping[str, Any]
    outcome: str
    net_points: float
    maximum_favorable_points: float
    maximum_adverse_points: float
    captured_profit_points: float
    peak_giveback_points: float
    holding_seconds: int
    break_even_exit: bool
    transaction_cost_points: float
    cross_market_context_id: str
    future_data_used: bool = False
    outcome_evaluation_uses_subsequent_closed_bars: bool = True
    data_quality_status: str = "PASS"

    def __post_init__(self) -> None:
        if not self.pattern_id.strip() or self.pattern_sequence <= 0 or not self.exit_policy_id.strip():
            raise ValueError("single-unit profit observation identity is required")
        if not self.policy_parameters:
            raise ValueError("exit policy parameters are required")
        if self.outcome not in {"WIN", "LOSS", "FLAT"}:
            raise ValueError("invalid single-unit profit outcome")
        numbers = (
            self.net_points, self.maximum_favorable_points, self.maximum_adverse_points,
            self.captured_profit_points, self.peak_giveback_points, self.transaction_cost_points,
        )
        if any(not math.isfinite(float(value)) for value in numbers):
            raise ValueError("single-unit profit values must be finite")
        if min(self.maximum_favorable_points, self.maximum_adverse_points, self.peak_giveback_points,
               self.transaction_cost_points, self.holding_seconds) < 0:
            raise ValueError("single-unit profit distances and holding time cannot be negative")
        if not self.cross_market_context_id.strip():
            raise ValueError("cross-market context is required")
        if self.future_data_used or self.data_quality_status != "PASS":
            raise ValueError("only leakage-free PASS profit evidence is eligible")
        if not self.outcome_evaluation_uses_subsequent_closed_bars:
            raise ValueError("outcome evaluation requires subsequent closed bars")

    @property
    def research_key(self) -> str:
        return _research_key(self.research_identity, self.shape_signature)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["research_identity"] = self.research_identity.as_dict()
        payload["shape_signature"] = self.shape_signature.as_dict()
        payload["policy_parameters"] = dict(self.policy_parameters)
        return payload


@dataclass(frozen=True)
class SingleUnitProfitResearchStandard:
    standard_id: str
    standard_version: str
    research_key: str
    selected_exit_policy_id: str
    policy_parameters: Mapping[str, Any]
    pattern_count: int
    samples: int
    win_rate: float
    win_rate_confidence_95_low: float
    expectancy_points: float
    net_points: float
    profit_capture_ratio: float
    average_peak_giveback_points: float
    break_even_exit_rate: float
    average_holding_seconds: float
    average_transaction_cost_points: float
    research_status: str = "RESEARCH_ACTIVE"
    production_usable: bool = False
    automatic_production_promotion_allowed: bool = False
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["policy_parameters"] = dict(self.policy_parameters)
        payload["standard_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class InitialCapitalObservation:
    pattern_id: str
    pattern_sequence: int
    research_identity: PatternResearchIdentity
    shape_signature: PatternShapeSignature
    starting_capital_usd: float
    required_margin_usd: float
    approved_risk_usd: float
    maximum_adverse_equity_usd: float
    realized_pnl_usd: float
    transaction_cost_usd: float
    survived: bool
    margin_failure: bool
    risk_budget_failure: bool
    cross_market_context_id: str
    lot: float = 0.01
    future_data_used: bool = False
    outcome_evaluation_uses_subsequent_closed_bars: bool = True
    data_quality_status: str = "PASS"

    def __post_init__(self) -> None:
        if not self.pattern_id.strip() or self.pattern_sequence <= 0:
            raise ValueError("initial-capital observation identity is required")
        values = (
            self.starting_capital_usd, self.required_margin_usd, self.approved_risk_usd,
            self.maximum_adverse_equity_usd, self.realized_pnl_usd,
            self.transaction_cost_usd, self.lot,
        )
        if any(not math.isfinite(float(value)) for value in values):
            raise ValueError("initial-capital values must be finite")
        if self.starting_capital_usd <= 0 or self.lot != 0.01:
            raise ValueError("initial-capital research starts with exactly one 0.01 lot")
        if min(self.required_margin_usd, self.approved_risk_usd,
               self.maximum_adverse_equity_usd, self.transaction_cost_usd) < 0:
            raise ValueError("initial-capital costs cannot be negative")
        if not self.cross_market_context_id.strip():
            raise ValueError("cross-market context is required")
        if self.future_data_used or self.data_quality_status != "PASS":
            raise ValueError("only leakage-free PASS capital evidence is eligible")
        if not self.outcome_evaluation_uses_subsequent_closed_bars:
            raise ValueError("outcome evaluation requires subsequent closed bars")

    @property
    def research_key(self) -> str:
        return _research_key(self.research_identity, self.shape_signature)

    @property
    def candidate_id(self) -> str:
        return f"CAPITAL-{self.starting_capital_usd:.2f}"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["research_identity"] = self.research_identity.as_dict()
        payload["shape_signature"] = self.shape_signature.as_dict()
        payload["candidate_id"] = self.candidate_id
        return payload


@dataclass(frozen=True)
class InitialCapitalResearchStandard:
    standard_id: str
    standard_version: str
    research_key: str
    pattern_count: int
    technical_minimum_usd: float | None
    operational_capital_usd: float | None
    robust_capital_usd: float | None
    selected_status: str
    candidate_metrics: tuple[Mapping[str, Any], ...]
    lot: float = 0.01
    production_usable: bool = False
    automatic_production_promotion_allowed: bool = False
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidate_metrics"] = [dict(value) for value in self.candidate_metrics]
        payload["standard_checksum"] = _checksum(payload)
        return payload


class _CumulativeStandardizer:
    size = 1000

    def __init__(self, dataset: AppendOnlyResearchDataset) -> None:
        self.dataset = dataset

    def _latest(self, dataset_name: str) -> dict[str, dict[str, Any]]:
        states: dict[str, dict[str, Any]] = {}
        for envelope in self.dataset.records(dataset_name):
            record = dict(envelope.get("record", {}))
            key = str(record.get("research_key", ""))
            if key:
                states[key] = record
        return states


class SingleUnitProfitStandardizer(_CumulativeStandardizer):
    def evaluate(self, observations: Sequence[SingleUnitProfitObservation]) -> tuple[dict[str, Any], ...]:
        states = self._latest("single_unit_profit_cumulative_aggregates")
        groups: dict[str, list[SingleUnitProfitObservation]] = {}
        unique: dict[tuple[str, str, str], SingleUnitProfitObservation] = {}
        for row in observations:
            row.__post_init__()
            identity = (row.research_key, row.pattern_id, row.exit_policy_id)
            if identity in unique and unique[identity] != row:
                raise ValueError("conflicting duplicate single-unit profit observation")
            unique[identity] = row
        for row in unique.values():
            groups.setdefault(row.research_key, []).append(row)

        results: list[dict[str, Any]] = []
        for key, all_rows in sorted(groups.items()):
            prior = states.get(key, {})
            prior_count = int(prior.get("processed_pattern_count", 0))
            last_sequence = int(prior.get("last_pattern_sequence", 0))
            rows = [row for row in all_rows if row.pattern_sequence > last_sequence]
            order = sorted({(row.pattern_sequence, row.pattern_id) for row in rows})
            stats = {str(k): dict(v) for k, v in dict(prior.get("policy_stats", {})).items()}
            for complete in range(self.size, len(order) + 1, self.size):
                pattern_slice = order[complete-self.size:complete]
                ids = {pattern_id for _, pattern_id in pattern_slice}
                batch = [row for row in rows if row.pattern_id in ids]
                policies = sorted({row.exit_policy_id for row in batch})
                if not policies or any(sum(row.exit_policy_id == policy for row in batch) != len(ids) for policy in policies):
                    results.append({"status":"QUARANTINED","reason":"profit_policy_pattern_coverage_incomplete","research_key":key})
                    continue
                for policy in policies:
                    items = [row for row in batch if row.exit_policy_id == policy]
                    value = stats.setdefault(policy, {
                        "policy_parameters": dict(items[0].policy_parameters), "samples":0, "wins":0,
                        "net":0.0, "mfe":0.0, "captured":0.0, "giveback":0.0,
                        "break_even":0, "holding":0, "cost":0.0,
                    })
                    value["samples"] += len(items)
                    value["wins"] += sum(row.outcome == "WIN" for row in items)
                    value["net"] += sum(row.net_points for row in items)
                    value["mfe"] += sum(row.maximum_favorable_points for row in items)
                    value["captured"] += sum(max(0.0, row.captured_profit_points) for row in items)
                    value["giveback"] += sum(row.peak_giveback_points for row in items)
                    value["break_even"] += sum(row.break_even_exit for row in items)
                    value["holding"] += sum(row.holding_seconds for row in items)
                    value["cost"] += sum(row.transaction_cost_points for row in items)
                ranked: list[tuple[float, float, float, float, str, dict[str, Any]]] = []
                for policy, value in stats.items():
                    samples = int(value["samples"]); wins = int(value["wins"])
                    expectancy = float(value["net"]) / samples
                    capture = float(value["captured"]) / max(float(value["mfe"]), 1e-12)
                    giveback = float(value["giveback"]) / samples
                    ranked.append((_wilson_low(wins, samples), expectancy, capture, -giveback, policy, value))
                ranked.sort(reverse=True)
                low, expectancy, capture, _, policy, value = ranked[0]
                cumulative = prior_count + complete
                version = f"B{cumulative//self.size:06d}-P{max(sequence for sequence, _ in pattern_slice):012d}"
                standard = SingleUnitProfitResearchStandard(
                    standard_id="PROFIT-ONE-" + _checksum({"research_key":key})[:16].upper(),
                    standard_version=version, research_key=key, selected_exit_policy_id=policy,
                    policy_parameters=dict(value["policy_parameters"]), pattern_count=cumulative,
                    samples=int(value["samples"]), win_rate=round(int(value["wins"])/int(value["samples"])*100,8),
                    win_rate_confidence_95_low=round(low*100,8), expectancy_points=round(expectancy,8),
                    net_points=round(float(value["net"]),8), profit_capture_ratio=round(capture,8),
                    average_peak_giveback_points=round(float(value["giveback"])/int(value["samples"]),8),
                    break_even_exit_rate=round(int(value["break_even"])/int(value["samples"])*100,8),
                    average_holding_seconds=round(int(value["holding"])/int(value["samples"]),8),
                    average_transaction_cost_points=round(float(value["cost"])/int(value["samples"]),8),
                )
                aggregate = {"schema_version":"single-unit-profit-cumulative.v1","research_key":key,
                    "processed_pattern_count":cumulative,"last_pattern_sequence":max(sequence for sequence,_ in pattern_slice),
                    "policy_stats":stats,"standard_version":version}
                self.dataset.append("single_unit_profit_research_standards", standard.as_dict())
                self.dataset.append("single_unit_profit_cumulative_aggregates", aggregate)
                result = {"status":"RESEARCH_STANDARD_UPDATED","reason":"new_1000_merged_into_cumulative_profit_standard",
                          "research_key":key,"standard":standard.as_dict()}
                self.dataset.append("single_unit_profit_batch_evaluations", result)
                results.append(result)
                prior = aggregate
            if len(order) < self.size or len(order) % self.size:
                results.append({"status":"WAITING","reason":"next_cumulative_1000_profit_patterns_incomplete",
                                "research_key":key,"covered_patterns":prior_count+len(order)})
        return tuple(results)


class InitialCapitalStandardizer(_CumulativeStandardizer):
    def evaluate(self, observations: Sequence[InitialCapitalObservation]) -> tuple[dict[str, Any], ...]:
        states = self._latest("initial_capital_cumulative_aggregates")
        groups: dict[str, list[InitialCapitalObservation]] = {}
        unique: dict[tuple[str, str, str], InitialCapitalObservation] = {}
        for row in observations:
            row.__post_init__()
            identity = (row.research_key, row.pattern_id, row.candidate_id)
            if identity in unique and unique[identity] != row:
                raise ValueError("conflicting duplicate initial-capital observation")
            unique[identity] = row
        for row in unique.values():
            groups.setdefault(row.research_key, []).append(row)
        results: list[dict[str, Any]] = []
        for key, all_rows in sorted(groups.items()):
            prior = states.get(key, {})
            prior_count = int(prior.get("processed_pattern_count", 0))
            last_sequence = int(prior.get("last_pattern_sequence", 0))
            rows = [row for row in all_rows if row.pattern_sequence > last_sequence]
            order = sorted({(row.pattern_sequence, row.pattern_id) for row in rows})
            stats = {str(k): dict(v) for k,v in dict(prior.get("candidate_stats", {})).items()}
            for complete in range(self.size, len(order)+1, self.size):
                pattern_slice = order[complete-self.size:complete]
                ids = {pattern_id for _,pattern_id in pattern_slice}
                batch = [row for row in rows if row.pattern_id in ids]
                candidates = sorted({row.candidate_id for row in batch})
                if not candidates or any(sum(row.candidate_id == candidate for row in batch) != len(ids) for candidate in candidates):
                    results.append({"status":"QUARANTINED","reason":"capital_candidate_pattern_coverage_incomplete","research_key":key})
                    continue
                for candidate in candidates:
                    items = sorted((row for row in batch if row.candidate_id == candidate), key=lambda row: row.pattern_sequence)
                    capital = float(items[0].starting_capital_usd)
                    value = stats.setdefault(candidate, {"starting_capital_usd":capital,"samples":0,"survived":0,
                        "margin_failures":0,"risk_failures":0,"net_pnl":0.0,"cumulative_pnl":0.0,
                        "equity_peak":capital,"max_drawdown_usd":0.0,"maximum_margin_usd":0.0,
                        "maximum_adverse_usd":0.0,"cost":0.0})
                    for row in items:
                        equity_before = capital + float(value["cumulative_pnl"])
                        value["equity_peak"] = max(float(value["equity_peak"]), equity_before)
                        trough = equity_before - row.maximum_adverse_equity_usd - row.transaction_cost_usd
                        value["max_drawdown_usd"] = max(float(value["max_drawdown_usd"]), float(value["equity_peak"])-trough)
                        value["cumulative_pnl"] += row.realized_pnl_usd
                        value["samples"] += 1; value["survived"] += int(row.survived)
                        value["margin_failures"] += int(row.margin_failure)
                        value["risk_failures"] += int(row.risk_budget_failure)
                        value["net_pnl"] += row.realized_pnl_usd
                        value["maximum_margin_usd"] = max(float(value["maximum_margin_usd"]), row.required_margin_usd)
                        value["maximum_adverse_usd"] = max(float(value["maximum_adverse_usd"]), row.maximum_adverse_equity_usd)
                        value["cost"] += row.transaction_cost_usd
                metrics: list[dict[str, Any]] = []
                for candidate,value in stats.items():
                    samples=int(value["samples"]); survived=int(value["survived"]); capital=float(value["starting_capital_usd"])
                    metrics.append({"candidate_id":candidate,"starting_capital_usd":capital,"samples":samples,
                        "survival_rate":round(survived/samples*100,8),"survival_confidence_95_low":round(_wilson_low(survived,samples)*100,8),
                        "margin_failure_rate":round(int(value["margin_failures"])/samples*100,8),
                        "risk_budget_failure_rate":round(int(value["risk_failures"])/samples*100,8),
                        "maximum_drawdown_usd":round(float(value["max_drawdown_usd"]),8),
                        "maximum_drawdown_percent":round(float(value["max_drawdown_usd"])/capital*100,8),
                        "maximum_margin_usd":round(float(value["maximum_margin_usd"]),8),
                        "maximum_adverse_usd":round(float(value["maximum_adverse_usd"]),8),
                        "net_pnl_usd":round(float(value["net_pnl"]),8),"transaction_cost_usd":round(float(value["cost"]),8)})
                metrics.sort(key=lambda item:item["starting_capital_usd"])
                technical = next((m for m in metrics if m["margin_failure_rate"]==0 and m["survival_rate"]==100), None)
                operational = next((m for m in metrics if m["survival_confidence_95_low"]>=99 and m["risk_budget_failure_rate"]==0 and m["maximum_drawdown_percent"]<=30), None)
                robust = next((m for m in metrics if m["survival_confidence_95_low"]>=99.5 and m["risk_budget_failure_rate"]==0 and m["maximum_drawdown_percent"]<=20), None)
                cumulative=prior_count+complete
                version=f"B{cumulative//self.size:06d}-P{max(sequence for sequence,_ in pattern_slice):012d}"
                standard=InitialCapitalResearchStandard(
                    standard_id="CAPITAL-ONE-"+_checksum({"research_key":key})[:16].upper(),standard_version=version,
                    research_key=key,pattern_count=cumulative,
                    technical_minimum_usd=technical["starting_capital_usd"] if technical else None,
                    operational_capital_usd=operational["starting_capital_usd"] if operational else None,
                    robust_capital_usd=robust["starting_capital_usd"] if robust else None,
                    selected_status="ROBUST" if robust else "OPERATIONAL" if operational else "TECHNICAL_MINIMUM" if technical else "INSUFFICIENT",
                    candidate_metrics=tuple(metrics),
                )
                aggregate={"schema_version":"initial-capital-cumulative.v1","research_key":key,
                    "processed_pattern_count":cumulative,"last_pattern_sequence":max(sequence for sequence,_ in pattern_slice),
                    "candidate_stats":stats,"standard_version":version}
                self.dataset.append("initial_capital_research_standards",standard.as_dict())
                self.dataset.append("initial_capital_cumulative_aggregates",aggregate)
                result={"status":"RESEARCH_STANDARD_UPDATED","reason":"new_1000_merged_into_cumulative_initial_capital_standard",
                        "research_key":key,"standard":standard.as_dict()}
                self.dataset.append("initial_capital_batch_evaluations",result); results.append(result); prior=aggregate
            if len(order)<self.size or len(order)%self.size:
                results.append({"status":"WAITING","reason":"next_cumulative_1000_capital_patterns_incomplete",
                                "research_key":key,"covered_patterns":prior_count+len(order)})
        return tuple(results)


def identity_from_mapping(value: Mapping[str, Any]) -> PatternResearchIdentity:
    return PatternResearchIdentity(**{name:value[name] for name in PatternResearchIdentity.__dataclass_fields__})


def shape_from_mapping(value: Mapping[str, Any]) -> PatternShapeSignature:
    raw=dict(value); raw.pop("shape_bucket_key",None)
    return PatternShapeSignature(**{name:raw[name] for name in PatternShapeSignature.__dataclass_fields__})


def profit_observation_from_mapping(value: Mapping[str, Any]) -> SingleUnitProfitObservation:
    raw=dict(value); identity=identity_from_mapping(raw.pop("research_identity")); shape=shape_from_mapping(raw.pop("shape_signature"))
    return SingleUnitProfitObservation(**raw,research_identity=identity,shape_signature=shape)


def capital_observation_from_mapping(value: Mapping[str, Any]) -> InitialCapitalObservation:
    raw=dict(value); raw.pop("candidate_id",None); identity=identity_from_mapping(raw.pop("research_identity")); shape=shape_from_mapping(raw.pop("shape_signature"))
    return InitialCapitalObservation(**raw,research_identity=identity,shape_signature=shape)
