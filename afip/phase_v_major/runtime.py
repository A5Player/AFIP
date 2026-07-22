from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping

from afip.automatic_research_runtime import AutomaticResearchRuntime
from .policy_promotion import CertifiedPolicyPromotion

SCHEMA_VERSION = "AFIP-PHASE-V-MAJOR-V1"
MODES = {"DATA_ONLY", "RESEARCH_ONLY", "SHADOW_EXECUTION", "DEMO_EXECUTION", "LIVE_EXECUTION"}


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


@dataclass(frozen=True)
class PhaseVMajorStatus:
    schema_version: str
    status: str
    stage: str
    reason: str
    mode: str
    updated_at_utc: str
    historical_catch_up_complete: bool
    continuous_research_enabled: bool
    research_baseline_certified: bool
    live_ready: bool
    live_execution_armed: bool
    live_execution_enabled: bool
    order_send_called: bool
    automatic_research: dict[str, Any]
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PhaseVMajorRuntime:
    """Historical-to-current research authority without implicit order authority."""

    def __init__(self, root: str | Path = ".", config_path: str | Path = "config/phase_v_major.json") -> None:
        self.root = Path(root).resolve()
        self.config_path = self.root / config_path
        self.status_path = self.root / "runtime/research/phase_v_major_status.json"
        self.arm_path = self.root / "runtime/control/phase_v_live_execution.arm"

    def config(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "mode": "DATA_ONLY",
            "maximum_replay_bars_per_cycle": 5000,
            "minimum_usable_bars": 1000,
            "require_replay_completion": True,
            "require_manual_live_arm": True,
            "continuous_interval_seconds": 300,
        }
        if self.config_path.exists():
            value = json.loads(self.config_path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                defaults.update(value)
        mode = str(defaults.get("mode", "DATA_ONLY")).upper()
        if mode not in MODES:
            raise ValueError(f"unsupported Phase V mode: {mode}")
        defaults["mode"] = mode
        return defaults

    def _research_certified(self, summary: Mapping[str, Any], config: Mapping[str, Any]) -> tuple[bool, list[str]]:
        blockers: list[str] = []
        usable = int(summary.get("usable_bars", 0) or 0)
        if usable < int(config["minimum_usable_bars"]):
            blockers.append("minimum_usable_bars_not_met")
        if bool(config.get("require_replay_completion", True)) and not bool(summary.get("replay_completed", False)):
            blockers.append("historical_replay_not_complete")
        if int(summary.get("gap_ranges_detected", 0) or 0) > 0:
            blockers.append("historical_gap_ranges_detected")
        if int(summary.get("missing_bars_detected", 0) or 0) > 0:
            blockers.append("historical_missing_bars_detected")
        return not blockers, blockers

    def run_once(self, *, collect_mt5: bool = True) -> PhaseVMajorStatus:
        config = self.config()
        maximum = max(500, int(config["maximum_replay_bars_per_cycle"]))
        promotion = CertifiedPolicyPromotion(self.root).promote_latest()
        research = AutomaticResearchRuntime(self.root, progress=print).run(
            collect_mt5_when_needed=collect_mt5,
            maximum_replay_bars=maximum,
        ).as_dict()
        certified, blockers = self._research_certified(research, config)
        historical_complete = bool(research.get("replay_completed", False)) and not blockers
        arm_present = self.arm_path.exists()
        requested_live = config["mode"] == "LIVE_EXECUTION"
        live_ready = certified and historical_complete
        armed = arm_present and requested_live
        live_enabled = live_ready and armed and not bool(config.get("require_manual_live_arm", True) and not arm_present)
        if live_enabled:
            status, stage, reason = "READY", "LIVE_READY", "certified_and_manually_armed"
        elif live_ready:
            status, stage, reason = "READY", "LIVE_READY", "manual_live_arm_required"
        elif research.get("status") in {"READY", "REVIEW"}:
            status, stage, reason = "RUNNING", "CONTINUOUS_RESEARCH", "historical_catch_up_or_certification_in_progress"
        else:
            status, stage, reason = "WAITING", "DATA_LOADING", str(research.get("reason", "research_not_ready"))
        payload = PhaseVMajorStatus(
            schema_version=SCHEMA_VERSION,
            status=status,
            stage=stage,
            reason=reason,
            mode=config["mode"],
            updated_at_utc=_utc(),
            historical_catch_up_complete=historical_complete,
            continuous_research_enabled=True,
            research_baseline_certified=certified,
            live_ready=live_ready,
            live_execution_armed=armed,
            live_execution_enabled=live_enabled,
            order_send_called=False,
            automatic_research={**research, "policy_promotion": promotion},
            blockers=tuple(blockers),
        )
        _atomic_json(self.status_path, payload.as_dict())
        return payload

    def arm_live(self, confirmation: str) -> Path:
        if confirmation.strip() != "ARM AFIP LIVE EXECUTION":
            raise ValueError("exact confirmation required: ARM AFIP LIVE EXECUTION")
        self.arm_path.parent.mkdir(parents=True, exist_ok=True)
        self.arm_path.write_text(json.dumps({"armed_at_utc": _utc(), "confirmation": confirmation}, indent=2), encoding="utf-8")
        return self.arm_path

    def disarm_live(self) -> bool:
        if not self.arm_path.exists():
            return False
        self.arm_path.unlink()
        return True
