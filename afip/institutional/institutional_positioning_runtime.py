"""Runtime orchestration for institutional positioning data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from afip.institutional.comex_inventory_runtime import ComexInventoryRuntime
from afip.institutional.cot_positioning import CotPositioningEngine
from afip.institutional.etf_gold_flow_runtime import EtfGoldFlowRuntime
from afip.institutional.institutional_positioning_consensus import InstitutionalPositioningConsensusEngine
from afip.institutional.open_interest_runtime import OpenInterestRuntime
from afip.institutional.provider import EmptyInstitutionalDataProvider, InstitutionalDataProvider


@dataclass(frozen=True)
class InstitutionalPositioningRuntimeState:
    """Complete institutional positioning runtime state."""

    status: str
    source: str
    observed_at: datetime
    cot_positioning: dict[str, object]
    open_interest: dict[str, object]
    etf_gold_flow: dict[str, object]
    comex_inventory: dict[str, object]
    institutional_positioning: dict[str, object]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "source": self.source,
            "observed_at": self.observed_at.isoformat(),
            "cot_positioning": dict(self.cot_positioning),
            "open_interest": dict(self.open_interest),
            "etf_gold_flow": dict(self.etf_gold_flow),
            "comex_inventory": dict(self.comex_inventory),
            "institutional_positioning": dict(self.institutional_positioning),
            "reason": self.reason,
        }


class InstitutionalPositioningRuntime:
    """Build a deterministic institutional positioning state from provider data."""

    def __init__(self, provider: InstitutionalDataProvider | None = None) -> None:
        self._provider = provider or EmptyInstitutionalDataProvider()
        self._cot_engine = CotPositioningEngine()
        self._open_interest_runtime = OpenInterestRuntime()
        self._etf_flow_runtime = EtfGoldFlowRuntime()
        self._comex_runtime = ComexInventoryRuntime()
        self._consensus_engine = InstitutionalPositioningConsensusEngine()

    def run(self, observed_at: datetime | None = None) -> InstitutionalPositioningRuntimeState:
        observed_at = observed_at or datetime.now(timezone.utc)
        provider_result = self._provider.fetch_values(observed_at=observed_at)
        values = provider_result.values
        cot_state = self._cot_engine.assess_dict(values)
        oi_state = self._open_interest_runtime.assess_dict(values)
        etf_state = self._etf_flow_runtime.assess_dict(values)
        comex_state = self._comex_runtime.assess_dict(values)
        positioning_state = self._consensus_engine.combine_dict(cot_state, oi_state, etf_state, comex_state)
        status = "INSTITUTIONAL_POSITIONING_RUNTIME_READY" if values else "INSTITUTIONAL_POSITIONING_RUNTIME_EMPTY"
        return InstitutionalPositioningRuntimeState(
            status=status,
            source=provider_result.source,
            observed_at=provider_result.observed_at,
            cot_positioning=cot_state,
            open_interest=oi_state,
            etf_gold_flow=etf_state,
            comex_inventory=comex_state,
            institutional_positioning=positioning_state,
            reason="institutional_positioning_runtime_ready" if values else "institutional_positioning_provider_empty",
        )

    def run_dict(self, observed_at: datetime | None = None) -> dict[str, object]:
        return self.run(observed_at=observed_at).as_dict()
