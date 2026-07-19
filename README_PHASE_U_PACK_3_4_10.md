# AFIP Phase U Pack 3.4.10
Continuous Cross-Market Research Runtime Collector.

- Real-source only
- Append-only observations
- Evidence and influence research
- Minimum interval 60 seconds
- No execution authority
- All relationships remain RESEARCH_ONLY

Run one cycle:
`powershell -ExecutionPolicy Bypass -File .\RUN_PHASE_U_PACK_3_4_10_ONCE.ps1`

Continuous:
`powershell -ExecutionPolicy Bypass -File .\START_PHASE_U_PACK_3_4_10_CONTINUOUS.ps1 -IntervalSeconds 300`

Stop:
`powershell -ExecutionPolicy Bypass -File .\STOP_PHASE_U_PACK_3_4_10_CONTINUOUS.ps1`
