# AFIP V1 Runtime Certification Repair Pack 2

Patch-only repair for the 17 regression failures reported after Control Center Pack 1.

Repairs:
- Restores the existing sequential, short-lived, process-isolated MT5 router authority.
- Removes the conflicting one-process-per-profile worker architecture introduced by an earlier repair pack.
- Imports the existing `reclaim_stale_lock` authority used by the demo execution gateway.
- Keeps injected MT5 test adapters on profile-local locks so regression tests cannot contend with a live production routing lock.

This pack does not modify capital gating, lot sizing, SL, TP, confidence, trading-cost thresholds, or order policy.
