# AFIP V1 Final Capital Authority Execution Integration Final Pack

Purpose:
Integrate approved Capital Authority results into execution flow.

Final execution contract:

Decision
 -> Confidence Authority
 -> Capital Authority
 -> Lot Authority
 -> Risk Approval
 -> Execution Gateway
 -> MT5 Router

Rules:
- No fixed lot bypass.
- No forced unit bypass.
- P1-P4 share the same execution pipeline.
- Profile differences come from configuration.
