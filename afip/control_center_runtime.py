"""Passive AFIP startup/control-center status projection.

This module never starts trading, research, MT5, or dashboard processes. It only
records deterministic observability state and projects existing runtime files.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "afip-control-center.v2"
STAGES = (
    "INITIALIZING",
    "VALIDATING_CONFIGURATION",
    "LOADING_PROFILE_CONFIGURATION",
    "CHECKING_RUNTIME_DIRECTORIES",
    "CHECKING_MT5_TERMINALS",
    "CHECKING_MARKET_DATA",
    "CHECKING_RESEARCH_STORAGE",
    "CHECKING_EXECUTION_AUTHORITY",
    "BUILDING_DASHBOARDS",
    "READY",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}


def atomic_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)
    return path


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value not in (None, "", "DATA_UNAVAILABLE", "NOT_RECORDED"):
            return value
    return default


def _sum_timeframe_field(evidence: Mapping[str, Any], field: str) -> int:
    total = 0
    for row in evidence.values():
        if not isinstance(row, Mapping):
            continue
        try:
            total += int(row.get(field, 0) or 0)
        except (TypeError, ValueError):
            continue
    return total


@dataclass(frozen=True)
class StartupStatus:
    schema_version: str
    status: str
    current_stage: str
    progress_percent: float
    started_at: str
    updated_at: str
    completed_at: str | None
    elapsed_seconds: float
    stages_total: int
    stages_completed: int
    current_message: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    execution_authority_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["warnings"] = list(self.warnings)
        value["errors"] = list(self.errors)
        return value


class ControlCenterRuntime:
    """Read-only projection over existing AFIP runtime artifacts."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.root = Path(project_root).resolve()
        self.directory = self.root / "runtime" / "control_center"
        self.status_path = self.directory / "startup_status.json"
        self.events_path = self.directory / "startup_events.jsonl"

    def write_startup(self, stage: str, *, status: str = "RUNNING", message: str = "", warnings: tuple[str, ...] = (), errors: tuple[str, ...] = ()) -> StartupStatus:
        stage = stage.upper().strip()
        if stage not in STAGES and stage not in {"DEGRADED", "FAILED", "STOPPED"}:
            raise ValueError(f"unsupported startup stage: {stage}")
        previous = read_json(self.status_path)
        now = utc_now()
        started = str(previous.get("started_at") or now)
        completed = STAGES.index(stage) + 1 if stage in STAGES else int(previous.get("stages_completed", 0) or 0)
        final_status = status.upper().strip()
        if errors:
            final_status = "FAILED"
        elif stage == "READY" and warnings:
            final_status = "DEGRADED"
        elif stage == "READY":
            final_status = "READY"
        progress = round(min(100.0, completed / len(STAGES) * 100.0), 2)
        value = StartupStatus(
            SCHEMA_VERSION, final_status, stage, progress, started, now,
            now if final_status in {"READY", "DEGRADED", "FAILED", "STOPPED"} else None,
            0.0, len(STAGES), completed, message or stage.replace("_", " ").title(),
            tuple(warnings), tuple(errors), False,
        )
        atomic_json(self.status_path, value.as_dict())
        self.directory.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"timestamp": now, "stage": stage, "status": final_status, "message": value.current_message}, ensure_ascii=False, sort_keys=True) + "\n")
        return value

    def _startup_projection(self, integration: Mapping[str, Any], dashboard: Mapping[str, Any]) -> dict[str, Any]:
        startup = read_json(self.status_path)
        if startup:
            return startup
        # Absence of the optional startup producer is a known state, not missing
        # data. Do not infer readiness or mutate runtime authority.
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "NOT_RECORDED",
            "current_stage": "STARTUP_STATUS_NOT_GENERATED",
            "progress_percent": 0.0,
            "current_message": "Startup producer has not recorded a lifecycle snapshot",
            "updated_at": _first(dashboard.get("updated_at_utc"), integration.get("updated_at_utc"), default="NOT_RECORDED"),
            "warnings": ["startup_status.json not generated"],
            "errors": [],
            "execution_authority_changed": False,
        }

    def _research_projection(self, automatic: Mapping[str, Any], engine: Mapping[str, Any], integration: Mapping[str, Any]) -> dict[str, Any]:
        integration_research = _mapping(integration.get("research_runtime"))
        integration_engine = _mapping(integration_research.get("engine"))
        phase_v = _mapping(engine.get("phase_v")) or _mapping(integration_engine.get("phase_v"))
        evidence = _mapping(automatic.get("replay_timeframe_evidence"))
        if not evidence:
            evidence = _mapping(_mapping(phase_v.get("automatic_research")).get("replay_timeframe_evidence"))
        timeframes = tuple(str(key) for key in evidence.keys())
        available = _sum_timeframe_field(evidence, "available_bars")
        covered = _sum_timeframe_field(evidence, "covered_bars_after_run")
        processed = _sum_timeframe_field(evidence, "bars_processed_this_run")
        missing = max(0, available - covered)
        gap_count = sum(1 for row in evidence.values() if isinstance(row, Mapping) and not bool(row.get("coverage_complete", False)))
        progress = round((covered / available * 100.0), 2) if available else 0.0
        return {
            "status": _first(engine.get("service_state"), engine.get("status"), integration_research.get("process_state"), automatic.get("status"), default="NOT_RECORDED"),
            "current_operation": _first(engine.get("current_activity"), engine.get("reason"), automatic.get("reason"), default="NOT_RECORDED"),
            "current_timeframe": ", ".join(timeframes) if timeframes else "NOT_RECORDED",
            "symbol": _first(automatic.get("symbol"), engine.get("symbol"), default="GOLD#" if evidence else "NOT_RECORDED"),
            "available_bars": available if evidence else "NOT_RECORDED",
            "processed_bars": processed if evidence else "NOT_RECORDED",
            "covered_bars": covered if evidence else "NOT_RECORDED",
            "missing_bars": missing if evidence else "NOT_RECORDED",
            "gap_count": gap_count if evidence else "NOT_RECORDED",
            "progress_percent": progress if evidence else "NOT_RECORDED",
            "queue_depth": _first(engine.get("queue_depth"), automatic.get("queue_depth"), default=0),
            "last_error": _first(engine.get("last_error"), default="NONE"),
            "updated_at": _first(engine.get("updated_at_utc"), engine.get("heartbeat_utc"), automatic.get("completed_at_utc"), automatic.get("started_at_utc"), default="NOT_RECORDED"),
            "pid": _first(engine.get("pid"), integration_research.get("pid"), default="NOT_RECORDED"),
            "cycles": _first(engine.get("cycles"), default=0),
            "source_status": _first(automatic.get("status"), default="NOT_RECORDED"),
        }

    def _dashboard_projection(self, dashboard: Mapping[str, Any]) -> dict[str, Any]:
        status = _first(dashboard.get("status"), default="NOT_RECORDED")
        updated = _first(dashboard.get("updated_at_utc"), dashboard.get("updated_at"), default="NOT_RECORDED")
        return {
            **dict(dashboard),
            "status": status,
            "last_generated_at": updated,
            "updated_at": updated,
            "process_state": status,
            "pid": _first(dashboard.get("pid"), dashboard.get("process_id"), default="NOT_RECORDED"),
        }


    def _runtime_authority_projection(self, integration: Mapping[str, Any]) -> dict[str, Any]:
        desired = read_json(self.root / "runtime" / "control" / "final_integration" / "desired_runtime_state.json")
        watchdog = read_json(self.root / "runtime" / "control" / "final_integration" / "runtime_watchdog_status.json")
        router = read_json(self.root / "runtime" / "execution" / "sequential_router_status.json")
        trading = _mapping(integration.get("trading_runtime"))
        router_pid = _first(router.get("pid"), trading.get("router_pid"), default="NOT_RECORDED")
        watchdog_pid = _first(watchdog.get("pid"), default="NOT_RECORDED")
        desired_state = str(_first(desired.get("state"), default="NOT_RECORDED")).upper()
        router_state = str(_first(router.get("status"), trading.get("status"), default="NOT_RECORDED")).upper()
        watchdog_state = str(_first(watchdog.get("status"), default="NOT_RECORDED")).upper()
        authority_status = "READY" if desired_state in {"RUNNING", "STOPPED"} else "NOT_RECORDED"
        duplicate_risk = "NONE_DETECTED"
        if desired_state == "STOPPED" and router_state in {"RUNNING", "BOOTING"}:
            duplicate_risk = "ROUTER_RUNNING_WHILE_DESIRED_STOPPED"
        return {
            "status": authority_status,
            "canonical_lifecycle_authority": "tools.afip_final_integration",
            "canonical_start": "START_AFIP.ps1",
            "canonical_stop": "STOP_AFIP.ps1",
            "canonical_status": "STATUS_AFIP.ps1",
            "safe_start_wrapper": "START_AFIP_SAFE.ps1",
            "operational_wrapper": "RUN_AFIP_V1_FINAL_OPERATIONAL_RUNTIME.ps1",
            "desired_state": desired_state,
            "desired_state_reason": _first(desired.get("reason"), default="NOT_RECORDED"),
            "router_state": router_state,
            "router_pid": router_pid,
            "watchdog_state": watchdog_state,
            "watchdog_pid": watchdog_pid,
            "duplicate_process_risk": duplicate_risk,
            "mt5_auto_launch_allowed": False,
            "execution_authority_changed": False,
            "source_paths": [
                "runtime/control/final_integration/desired_runtime_state.json",
                "runtime/control/final_integration/runtime_watchdog_status.json",
                "runtime/execution/sequential_router_status.json",
                "runtime/final_integration_status.json",
            ],
        }


    @staticmethod
    def _stage(name: str, status: Any, reason: Any = "NOT_RECORDED", *, value: Any = "NOT_RECORDED", source: str = "") -> dict[str, Any]:
        return {
            "stage": name,
            "status": _first(status, default="NOT_RECORDED"),
            "reason": _first(reason, default="NOT_RECORDED"),
            "value": _first(value, default="NOT_RECORDED"),
            "source": source or "NOT_RECORDED",
        }

    def _explain_profile(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        intelligence = _mapping(profile.get("intelligence_snapshot"))
        decision_trace = _mapping(intelligence.get("decision"))
        lot_trace = _mapping(profile.get("lot_authority_trace"))
        unit_results = profile.get("unit_results", [])
        if not isinstance(unit_results, list):
            unit_results = []
        latest_broker = unit_results[-1] if unit_results and isinstance(unit_results[-1], Mapping) else {}
        decision = _first(profile.get("decision"), profile.get("decision_action"), default="NOT_EVALUATED")
        confidence = _first(profile.get("confidence"), profile.get("decision_confidence"), default="NOT_EVALUATED")
        waiting = _first(profile.get("waiting_reason"), profile.get("gateway_reason"), profile.get("reason"), default="NONE")
        stages = [
            self._stage("MARKET_DATA", _first(profile.get("market_data_status"), profile.get("data_status"), default="NOT_RECORDED"), _first(profile.get("market_data_reason"), default="NOT_RECORDED"), source="runtime/profiles/{}/demo_execution_state.json".format(str(profile.get("profile_id", "")).lower())),
            self._stage("INTELLIGENCE", "EVALUATED" if intelligence else "NOT_RECORDED", _first(decision_trace.get("conflict_resolution_reason"), default="NOT_RECORDED"), value=_first(decision_trace.get("selected_scenario"), default="NOT_RECORDED"), source="intelligence_snapshot"),
            self._stage("DECISION", "EVALUATED" if decision != "NOT_EVALUATED" else "NOT_RECORDED", waiting, value=decision, source="demo_execution_state.json"),
            self._stage("CONFIDENCE", "EVALUATED" if confidence != "NOT_EVALUATED" else "NOT_RECORDED", _first(profile.get("confidence_reason"), default="NOT_RECORDED"), value=confidence, source="demo_execution_state.json"),
            self._stage("CAPITAL", "PASS" if _first(profile.get("capital_units"), default=0) not in (0, "0", "NOT_EVALUATED") else "BLOCKED_OR_NOT_EVALUATED", _first(profile.get("limiting_gate"), default="NOT_RECORDED"), value=_first(profile.get("available_capital"), default="NOT_EVALUATED"), source="lot_authority_trace" if lot_trace else "demo_execution_state.json"),
            self._stage("RISK", "PASS" if _first(profile.get("risk_units"), default=0) not in (0, "0", "NOT_EVALUATED") else "BLOCKED_OR_NOT_EVALUATED", _first(profile.get("risk_reason"), default="NOT_RECORDED"), value=_first(profile.get("risk_units"), default="NOT_EVALUATED"), source="demo_execution_state.json"),
            self._stage("EXECUTION", _first(profile.get("execution_outcome"), profile.get("gateway_status"), default="NOT_ATTEMPTED"), waiting, value=_first(profile.get("execution_batch_id"), default="NOT_ATTEMPTED"), source="demo_execution_state.json"),
            self._stage("BROKER", _first(latest_broker.get("status"), profile.get("order_status"), default="NOT_ATTEMPTED"), _first(latest_broker.get("comment"), profile.get("broker_comment"), default="NOT_RECORDED"), value=_first(latest_broker.get("retcode"), profile.get("mt5_result_code"), default="NOT_RECORDED"), source="unit_results" if unit_results else "demo_execution_state.json"),
        ]
        blockers = [row for row in stages if str(row["status"]).upper() in {"BLOCKED", "FAILED", "REJECTED", "BROKER_REJECTED", "PARTIAL_REJECTED", "AMBIGUOUS_BROKER_RESULT", "BLOCKED_OR_NOT_EVALUATED"}]
        return {
            "trace_id": _first(profile.get("execution_trace_id"), profile.get("decision_trace_id"), profile.get("execution_batch_id") if profile.get("execution_batch_id") not in {"NOT_ATTEMPTED", "NOT_RECORDED"} else None, default="NOT_RECORDED"),
            "decision": decision,
            "confidence": confidence,
            "primary_reason": waiting,
            "selected_scenario": _first(decision_trace.get("selected_scenario"), default="NOT_RECORDED"),
            "conflict_resolution_reason": _first(decision_trace.get("conflict_resolution_reason"), default="NOT_RECORDED"),
            "stages": stages,
            "first_blocking_stage": blockers[0]["stage"] if blockers else "NONE_RECORDED",
            "source_policy": "RUNTIME_ARTIFACTS_ONLY_NO_INVENTED_EXPLANATION",
        }

    @staticmethod
    def _position_explanation(position_care: Mapping[str, Any]) -> dict[str, Any]:
        records = position_care.get("records", []) if isinstance(position_care, Mapping) else []
        if not isinstance(records, list):
            records = []
        latest = records[-1] if records and isinstance(records[-1], Mapping) else {}
        decision = _mapping(latest.get("position_care"))
        action = _mapping(latest.get("mt5_action"))
        context = _mapping(latest.get("intelligence_context"))
        return {
            "status": _first(position_care.get("status"), default="NOT_RECORDED"),
            "ticket": _first(latest.get("ticket"), latest.get("position_ticket"), default="NOT_RECORDED"),
            "recommended_action": _first(decision.get("recommended_action"), default="NOT_EVALUATED"),
            "reason_codes": _first(decision.get("reason_codes"), default="NOT_EVALUATED"),
            "proposed_stop_price": _first(decision.get("proposed_stop_price"), default="NOT_EVALUATED"),
            "mt5_action_status": _first(action.get("status"), default="NOT_EVALUATED"),
            "mt5_action_reason": _first(action.get("reason"), action.get("comment"), default="NOT_EVALUATED"),
            "intelligence_scenario": _first(context.get("selected_scenario"), default="NOT_EVALUATED"),
            "intelligence_confidence": _first(context.get("decision_confidence"), default="NOT_EVALUATED"),
            "execution_trace_id": _first(latest.get("execution_trace_id"), default="NOT_RECORDED"),
            "source": "runtime/profiles/{profile}/production_activation/position_care_status.json",
        }

    def _runtime_observatory(self, authority: Mapping[str, Any], truth: Mapping[str, Any], research: Mapping[str, Any], dashboard: Mapping[str, Any], profiles: list[Mapping[str, Any]]) -> dict[str, Any]:
        profile_connections = [str(p.get("mt5_connection", p.get("connection_status", "NOT_RECORDED"))).upper() for p in profiles]
        mt5_status = "READY" if profile_connections and all(v in {"CONNECTED", "READY"} for v in profile_connections) else ("DEGRADED" if any(v in {"CONNECTED", "READY"} for v in profile_connections) else "NOT_RECORDED")
        components = [
            {"component":"RUNTIME_AUTHORITY","status":_first(authority.get("status"), default="NOT_RECORDED"),"reason":_first(authority.get("duplicate_process_risk"), default="NOT_RECORDED")},
            {"component":"RUNTIME_TRUTH","status":_first(truth.get("status"), default="NOT_RECORDED"),"reason":f"conflicts={truth.get('conflict_count','NOT_RECORDED')}; missing={truth.get('missing_authority_count','NOT_RECORDED')}"},
            {"component":"RESEARCH","status":_first(research.get("status"), default="NOT_RECORDED"),"reason":_first(research.get("current_operation"), default="NOT_RECORDED")},
            {"component":"DASHBOARD","status":_first(dashboard.get("status"), default="NOT_RECORDED"),"reason":_first(dashboard.get("updated_at"), default="NOT_RECORDED")},
            {"component":"MT5_PROFILES","status":mt5_status,"reason":", ".join(profile_connections) if profile_connections else "NOT_RECORDED"},
        ]
        critical = [row for row in components if str(row["status"]).upper() in {"FAILED", "CRITICAL", "CONFLICT"}]
        degraded = [row for row in components if str(row["status"]).upper() in {"DEGRADED", "WARNING", "NOT_RECORDED"}]
        return {
            "status": "CRITICAL" if critical else ("DEGRADED" if degraded else "HEALTHY"),
            "components": components,
            "critical_count": len(critical),
            "degraded_count": len(degraded),
            "execution_authority_changed": False,
            "mt5_auto_launch_allowed": False,
        }

    def snapshot(self) -> dict[str, Any]:
        integration = read_json(self.root / "runtime" / "final_integration_status.json")
        automatic = read_json(self.root / "runtime" / "research" / "automatic_research_status.json")
        engine = read_json(self.root / "runtime" / "research" / "research_engine_status.json")
        collection = read_json(self.root / "runtime" / "research" / "runtime_collection_summary.json")
        from afip.runtime_truth import build_runtime_truth
        runtime_truth = build_runtime_truth(self.root)
        dashboard_raw = read_json(self.root / "runtime" / "dashboard" / "dashboard_monitor_status.json")
        contract = read_json(self.root / "runtime" / "dashboard" / "dashboard_runtime.json")
        contract_profiles = {
            str(row.get("profile_id", "")).upper(): dict(row)
            for row in contract.get("profiles", [])
            if isinstance(row, Mapping)
        }
        integration_trading = _mapping(integration.get("trading_runtime"))
        integration_profiles = {
            str(row.get("profile_id", "")).upper(): dict(row)
            for row in integration_trading.get("profiles", [])
            if isinstance(row, Mapping)
        }
        from afip.four_profile_operations import FourProfileOperationalRuntime
        profile_config_path = self.root / "config" / "four_profile_demo.json"
        try:
            configured_profiles = FourProfileOperationalRuntime(profile_config_path).load()
            configured_modes = {item.profile_id: item.trading_mode for item in configured_profiles}
            mode_configuration_status = "READY"
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            configured_modes = {}
            mode_configuration_status = f"BLOCKED:{type(exc).__name__}"
        profiles: list[dict[str, Any]] = []
        for profile_id in ("p1", "p2", "p3", "p4"):
            pid = profile_id.upper()
            base = self.root / "runtime" / "profiles" / profile_id
            health = read_json(base / "mt5_health.json")
            execution = read_json(base / "demo_execution_state.json")
            status = read_json(base / "status.json")
            position_care = read_json(base / "production_activation" / "position_care_status.json")
            data = {}
            for source in (contract_profiles.get(pid, {}), health, status, execution, integration_profiles.get(pid, {})):
                data.update(source)
            login = str(_first(data.get("connected_account_login"), data.get("login"), data.get("account"), default=""))
            if login and "*" not in login:
                data["login"] = ("*" * max(0, len(login) - 4)) + login[-4:]
            elif login:
                data["login"] = login
            data["profile_id"] = pid
            data["trading_mode"] = _first(data.get("profile_trading_mode"), configured_modes.get(pid), default="NOT_CONFIGURED")
            data["trading_mode_allowed"] = _first(data.get("profile_trading_mode_allowed"), default="NOT_EVALUATED")
            data["trading_mode_reason"] = _first(data.get("profile_trading_mode_reason"), default="NOT_EVALUATED")
            data["execution_mode"] = _first(data.get("execution_mode"), data.get("execution"), integration_trading.get("execution"), default="NOT_RECORDED")
            data["connection_status"] = _first(data.get("connection_status"), data.get("mt5_connection"), default="NOT_RECORDED")
            data["mt5_connection"] = _first(data.get("mt5_connection"), data.get("connection_status"), default="NOT_RECORDED")
            data["decision"] = _first(data.get("decision"), data.get("decision_action"), default="NOT_EVALUATED")
            data["confidence"] = _first(data.get("confidence"), data.get("decision_confidence"), default="NOT_EVALUATED")
            data["waiting_reason"] = _first(data.get("waiting_reason"), data.get("gateway_reason"), data.get("reason"), default="NONE")
            data["execution_batch_id"] = _first(data.get("execution_batch_id"), default="NOT_ATTEMPTED")
            data["execution_outcome"] = _first(data.get("execution_outcome"), default="NOT_ATTEMPTED")
            data["execution_attempts"] = _first(data.get("execution_attempts"), default=0)
            data["execution_latency_ms"] = _first(data.get("execution_latency_ms"), default="NOT_RECORDED")
            data["retry_policy"] = _first(data.get("retry_policy"), default="NO_AUTOMATIC_RETRY_AFTER_AMBIGUOUS_OR_PARTIAL_SEND")
            data["reconciliation_required"] = bool(data.get("reconciliation_required", False))
            data["partial_execution"] = bool(data.get("partial_execution", False))
            data["remaining_units"] = _first(data.get("remaining_units"), default=0)
            data["account_balance"] = _first(data.get("account_balance"), data.get("balance"), default="NOT_RECORDED")
            data["account_equity"] = _first(data.get("account_equity"), data.get("equity"), default="NOT_RECORDED")
            data["available_capital"] = _first(data.get("available_capital"), default="NOT_EVALUATED")
            data["capital_basis"] = _first(data.get("capital_basis"), default="NOT_EVALUATED")
            data["capital_units"] = _first(data.get("capital_units"), default="NOT_EVALUATED")
            data["risk_units"] = _first(data.get("risk_units"), default="NOT_EVALUATED")
            data["confidence_units"] = _first(data.get("confidence_units"), data.get("confidence_maximum_units"), default="NOT_EVALUATED")
            data["profile_max_units"] = _first(data.get("profile_max_units"), default="NOT_EVALUATED")
            data["execution_safety_units"] = _first(data.get("execution_safety_units"), default="NOT_EVALUATED")
            data["lot_limiting_gate"] = _first(data.get("limiting_gate"), default="NOT_EVALUATED")
            data["lot_authority_policy"] = _first(data.get("capital_authority_policy"), data.get("policy_version"), default="NOT_EVALUATED")
            data["approved_lot_per_order"] = _first(data.get("approved_lot_per_order"), default="NOT_EVALUATED")
            data["total_approved_lot"] = _first(data.get("total_approved_lot"), data.get("total_allocated_lot"), default="NOT_EVALUATED")
            data["entry_mode"] = _first(data.get("entry_mode"), default="NOT_EVALUATED")
            data["trade_case_id"] = _first(data.get("trade_case_id"), default="NOT_EVALUATED")
            data["initial_units"] = _first(data.get("initial_units"), default="NOT_EVALUATED")
            data["reserved_units"] = _first(data.get("reserved_units"), default="NOT_EVALUATED")
            data["capacity_is_ceiling_not_target"] = bool(data.get("capacity_is_ceiling_not_target", True))
            intelligence_snapshot = _mapping(data.get("intelligence_snapshot"))
            activation_matrix = intelligence_snapshot.get("activation_matrix", ())
            if not isinstance(activation_matrix, (list, tuple)):
                activation_matrix = ()
            decision_trace = _mapping(intelligence_snapshot.get("decision"))
            data["intelligence_modules"] = len(activation_matrix) if activation_matrix else "NOT_EVALUATED"
            data["decision_conflict_reason"] = _first(decision_trace.get("conflict_resolution_reason"), default="NOT_EVALUATED")
            data["decision_scenario"] = _first(decision_trace.get("selected_scenario"), default="NOT_EVALUATED")
            care_records = position_care.get("records", []) if isinstance(position_care, Mapping) else []
            if not isinstance(care_records, list):
                care_records = []
            latest_care = care_records[-1] if care_records and isinstance(care_records[-1], Mapping) else {}
            care_decision = _mapping(latest_care.get("position_care"))
            care_context = _mapping(latest_care.get("intelligence_context"))
            care_mt5_action = _mapping(latest_care.get("mt5_action"))
            care_policy = _mapping(position_care.get("position_management_policy")) if isinstance(position_care, Mapping) else {}
            data["positions_evaluated"] = position_care.get("positions_evaluated", "NOT_EVALUATED") if position_care else "NOT_EVALUATED"
            data["position_care_action"] = _first(care_decision.get("recommended_action"), default="NOT_EVALUATED")
            data["position_care_reason"] = _first(care_decision.get("reason_codes"), default="NOT_EVALUATED")
            data["care_intelligence_scenario"] = _first(care_context.get("selected_scenario"), default="NOT_EVALUATED")
            data["care_intelligence_confidence"] = _first(care_context.get("decision_confidence"), default="NOT_EVALUATED")
            data["position_action_status"] = _first(care_mt5_action.get("status"), default="NOT_EVALUATED")
            data["position_action_reason"] = _first(care_mt5_action.get("reason"), care_mt5_action.get("comment"), default="NOT_EVALUATED")
            data["break_even_policy"] = _first(care_policy.get("break_even"), default="NOT_EVALUATED")
            data["trailing_policy"] = _first(care_policy.get("trailing"), default="NOT_EVALUATED")
            data["partial_close_policy"] = _first(care_policy.get("partial_close"), default="NOT_EVALUATED")
            data["pyramiding_policy"] = _first(care_policy.get("pyramiding"), default="NOT_EVALUATED")
            data["decision_explainability"] = self._explain_profile(data)
            data["position_explainability"] = self._position_explanation(position_care)
            profiles.append(data)
        dashboard = self._dashboard_projection(dashboard_raw)
        authority = self._runtime_authority_projection(integration)
        research_projection = {
            **self._research_projection(automatic, engine, integration),
            "trade_cases_written": collection.get("trade_cases_written", "NOT_RECORDED"),
            "holding_observations": collection.get("holding_observations", "NOT_RECORDED"),
            "exits_recorded": collection.get("exits_recorded", "NOT_RECORDED"),
            "research_bridge_status": collection.get("status", "NOT_RECORDED"),
            "single_unit_profit_pattern_observations": automatic.get("single_unit_profit_pattern_observations", 0),
            "initial_capital_pattern_observations": automatic.get("initial_capital_pattern_observations", 0),
            "research_standards_updated": automatic.get("research_standards_updated", 0),
            "market_structure_contexts": automatic.get("market_structure_contexts", {}),
        }
        observatory = self._runtime_observatory(authority, runtime_truth, research_projection, dashboard, profiles)
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now(),
            "startup": self._startup_projection(integration, dashboard_raw),
            "final_integration": integration,
            "runtime_authority": authority,
            "runtime_truth": runtime_truth,
            "research": research_projection,
            "profile_trading_modes": {
                "status": mode_configuration_status,
                "profiles": configured_modes,
                "account_activation_policy": "OPERATOR_STARTS_ONLY_THE_MT5_TERMINALS_TO_USE",
                "execution_authority_changed": False,
            },
            "explainability": {
                "policy": "RUNTIME_ARTIFACTS_ONLY_NO_INVENTED_EXPLANATION",
                "profiles": {str(row.get("profile_id", "UNKNOWN")): row.get("decision_explainability", {}) for row in profiles},
                "positions": {str(row.get("profile_id", "UNKNOWN")): row.get("position_explainability", {}) for row in profiles},
                "execution_authority_changed": False,
            },
            "runtime_observatory": observatory,
            "dashboard": dashboard,
            "profiles": profiles,
            "execution_authority_changed": False,
            "execution_authority": "EXISTING_AFIP_RUNTIME_ONLY",
        }
