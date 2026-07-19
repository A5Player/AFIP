# Run Guide

1. Stop active AFIP writers before overlaying the patch.
2. Extract the Direct Overlay ZIP into the AFIP repository root.
3. Review `config/cross_market_gold_intelligence.json`.
4. Open the target XM MT5 terminal and log in.
5. Run `RUN_PHASE_U_PACK_3_4_9.ps1`.
6. Open `runtime/dashboard/afip_dashboard.html` and select Cross-Market.
7. Leave the collector to run again on the desired operating schedule. Each run appends one verified observation to `observations.jsonl`.

The runtime never sends an order. A missing symbol or unavailable provider remains `DATA_UNAVAILABLE`.
