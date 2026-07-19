# AFIP Phase U Pack 3.4.9
## Financial Data Integrity & Intelligence Runtime Certification

This patch removes invented AFIP Bank values and adds real-source certification for P1-P4 financial state, intelligence sources, and cross-market gold research.

### Safety contract

- Missing financial or intelligence values are `DATA_UNAVAILABLE`.
- `READY`, `CONNECTED`, or `VERIFIED` requires source evidence.
- Cross-market research has no execution authority.
- Relationships remain `RESEARCH_ONLY` until evidence certification is implemented and passed.
- No fallback balance, equity, allocation, or placeholder intelligence connectivity.

### Runtime pipeline

Raw Data -> Normalized Data -> Feature Engineering -> Research Database -> Knowledge Database -> Certification -> Trading Intelligence.

Pack 3.4.9 collects and stores data at the Research Database stage. It does not skip certification.

### Real collection

Edit `config/cross_market_gold_intelligence.json` only when broker symbol aliases or the MT5 terminal path differ. Then run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_4_9.ps1
```

Outputs:

- `runtime/certification/financial_integrity.json`
- `runtime/certification/intelligence_sources.json`
- `runtime/research/cross_market/latest.json`
- `runtime/research/cross_market/observations.jsonl`
- `runtime/dashboard/afip_cross_market_intelligence_dashboard.html`

External data such as COT, ETF flow, macro releases, geopolitical events, central-bank purchases, and gold-mining AISC must enter through verified source snapshots. They remain unavailable until a real provider writes timestamped evidence.
