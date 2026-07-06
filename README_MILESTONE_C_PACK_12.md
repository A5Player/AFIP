# AFIP Production Milestone C Pack 12

## Trading Pattern Repository Foundation

This patch adds a compact trading pattern research layer for AFIP. It aggregates repeated trading outcomes into normalized pattern and setup records instead of storing duplicate raw rows.

## Added

- Trading pattern record normalization
- Compact trade outcome statistics
- Trading pattern repository
- Trading setup repository
- Pattern quality assessment
- Trading pattern runtime
- Production runtime entrypoint
- Pack 12 tests
- Run scripts

## Quality

- Financial terminology only
- No non-financial architecture naming
- Patch only
- Deterministic runtime
- Compact storage through aggregation
