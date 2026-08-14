"""A23 honest completion record for holding/exit research; no live authority."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from afip.historical_replay_research import AppendOnlyResearchDataset

@dataclass(frozen=True)
class A23HoldingExitCertification:
    status: str
    reason: str
    holding_exit_observations: int
    validation_observations: int
    validation_results: int
    robust_partitions: int
    rejected_partitions: int
    waiting_partitions: int
    append_only_verified: bool
    research_only: bool = True
    read_only: bool = True
    production_usable: bool = False
    automatic_promotion_allowed: bool = False
    execution_authority: str = "NONE"
    def as_dict(self) -> dict[str, object]: return asdict(self)

class A23HoldingExitCompletion:
    """Certify evidence availability, never production readiness or promotion."""
    _CHAINS=("a20_holding_exit_observations","a20_holding_exit_rankings",
             "a22_holding_exit_validation_observations","a22_holding_exit_validation_results")
    def __init__(self,dataset:AppendOnlyResearchDataset)->None:self.dataset=dataset
    def certify(self)->A23HoldingExitCertification:
        results=[dict(item["record"]) for item in self.dataset.records("a22_holding_exit_validation_results")]
        robust=sum(item.get("status")=="ROBUST" for item in results)
        rejected=sum(item.get("status")=="REJECTED" for item in results)
        waiting=sum(item.get("status")=="WAIT" for item in results)
        verified=all(self.dataset.verify(name) for name in self._CHAINS)
        available=robust>0 and verified
        item=A23HoldingExitCertification(
            status="RESEARCH_EVIDENCE_AVAILABLE" if available else "WAIT",
            reason="robust_blind_forward_partition_available" if available else "robust_blind_forward_evidence_not_available",
            holding_exit_observations=self.dataset.count("a20_holding_exit_observations"),
            validation_observations=self.dataset.count("a22_holding_exit_validation_observations"),
            validation_results=len(results),robust_partitions=robust,rejected_partitions=rejected,
            waiting_partitions=waiting,append_only_verified=verified)
        self.dataset.append("a23_holding_exit_certifications",item.as_dict())
        return item
