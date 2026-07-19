# AFIP Milestone T Pack 14

## Unattended Continuity, Restart Reconciliation and Recovery Supervision

Pack 14 adds a deterministic continuity boundary for network interruption, MT5 interruption, process restart and VPS restart. It compares live account state with the append-only ledger before position care or new risk may continue.

Core policy:

- interruption never authorizes assumptions about position state;
- restart requires account and position reconciliation;
- unknown or missing positions block continuation;
- a manual position enters a safe operating state;
- invalid audit-chain evidence requires operator attention;
- execution permission remains false.

The pack does not import MetaTrader5 and does not send, modify or close orders.
