# AFIP Milestone W Architecture — Pack W0

## Source inspection result

The repository already contains substantial Research, Replay, Decision, Capital, Risk, Position, Exit, Execution and Dashboard code. Milestone W must connect existing components; it must not create a parallel trading system.

## Canonical operational path

1. `FinalIntegrationRuntime` supervises the operational services and publishes `runtime/final_integration_status.json`.
2. `UnifiedResearchEngine` is the canonical continuous research service. It explicitly publishes `execution_authority=false` and `order_send_called=false`.
3. Existing Intelligence/Decision code remains the decision authority.
4. Existing Capital/Lot and Risk chains remain approval authorities.
5. `DemoExecutionGateway` remains the only verified Python source that reaches `mt5.order_send()`.
6. Dashboard code remains read-only and must display producer/runtime truth.

## Reusable modules

- `afip/final_integration/runtime.py`
- `afip/final_integration/research_engine.py`
- `afip/research_data_foundation/*`
- `afip/research_replay_engine/runtime.py`
- `afip/research_ranking/runtime.py`
- `afip/research_governance/runtime.py`
- existing `afip/decision*`, `afip/intelligence*`, capital, risk, position and exit modules
- `afip/demo_execution_gateway/runtime.py`
- `afip/dashboard_ui/*`

## Missing bridge

The missing production-safe bridge is a versioned, traceable, read-only Research Evidence envelope consumed by the existing Intelligence decision path. W1–W5 must build that bridge without granting Research execution, capital, risk or policy authority.

## Duplicate-risk findings

Many historical milestone runtimes and similarly named research/decision/dashboard modules remain for compatibility and certification. They are not automatically deleted. New Milestone W code must bind only to the locked owners in `config/milestone_w_authority_contract.json` and must not nominate another supervisor, execution gateway, or dashboard truth store.
