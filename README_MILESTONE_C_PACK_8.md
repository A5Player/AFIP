# Production Milestone C Pack 8 — Institutional Positioning Foundation

Pack 8 adds the institutional positioning foundation for AFIP using financial-market terminology only. The pack introduces provider contracts and deterministic offline adapters for COT-style positioning, open interest, ETF gold allocation flow, and COMEX inventory context.

## Added

- Institutional data provider contract
- Static and empty institutional providers
- COT positioning assessment
- Open interest participation assessment
- ETF gold flow assessment
- COMEX inventory assessment
- Institutional positioning consensus
- Production Milestone C institutional runtime
- Pack 8 tests and run scripts

## Design Notes

- No live paid API dependency is required.
- The provider contract supports free, paid, and replay providers in later packs.
- COT is treated as strategic context, not entry timing.
- Open interest is interpreted together with gold price change.
- ETF flows and COMEX inventory are normalized into a single institutional positioning view.

## Validation

- Pack test: 11 passed
- Full pytest: PASS
- Local quality check: PASS
- Financial naming: PASS
