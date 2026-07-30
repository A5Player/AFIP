# Milestone W Authority Matrix

| Domain | Current owner | Milestone W permission |
|---|---|---|
| Operational runtime | `FinalIntegrationRuntime` | Reuse only; no parallel supervisor |
| Research | `UnifiedResearchEngine` plus research foundation/replay/governance | Produce evidence only |
| Intelligence/Decision | Existing Intelligence and Decision runtime | Consume/review evidence and retain final decision authority |
| Capital/Lot | Existing Capital/Lot authority chain | Research cannot size or override |
| Risk | Existing Risk authority chain | Research cannot approve or override |
| Execution | `DemoExecutionGateway` | Only approved execution path may reach MT5 |
| Position/Exit action | Existing management, Risk and Execution authorities | Research recommendation only |
| Governance | Existing research governance | Required for promotion/material changes |
| Dashboard | `afip.dashboard_ui` and producer runtime truth | Read-only display |

Research must never call `order_check`, `order_send`, change lot, alter production thresholds, promote itself, or write an alternative runtime truth.
