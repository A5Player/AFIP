# AFIP Milestone S Pack 7.2.2 - P2 Position Limit Validation

This corrective patch preserves AFIP Position Policy V2.1 and validates the P2 maximum position size.

Confirmed policy:

- P1 maximum lot per order: 0.10
- P2 maximum lot per order: 1.00
- P3 maximum lot per order: 10.00
- P4 fixed research lot: 0.01
- P2 final capital tier: minimum balance 1,545,300 with three 1.00-lot units
- No P2 capital tier may contain a lot value above 1.00
- Values from 1.01 through 10.00 belong only to the P3 capital tiers

Apply and test:

```powershell
.\APPLY_MILESTONE_S_PACK_7_2_2.ps1
.\RUN_MILESTONE_S_PACK_7_2_2.ps1
python -m pytest -q
python tools/afip_local_quality_check.py
```

Do not commit until the full regression test and AFIP Local Quality Check both pass.
