# AFIP Position Ceiling Policy V2

## Authority model

AFIP separates capacity from intent:

1. **Confidence ceiling** defines the maximum Unit count permitted for the signal.
2. **Balance tier** defines the maximum lot size per Unit and available profile slots.
3. **Profile** defines growth speed and the permanent risk ceiling.
4. **Intelligence request** defines how many Units are actually requested now.
5. Risk, margin, trading cost, duplicate-signal and execution gates may reduce or block the request.

A ceiling is never an instruction to fill every available Unit.

## Confidence ceilings

- Below 98.0: 0 Units
- 98.0–98.49: maximum 1 Unit
- 98.5–99.49: maximum 2 Units
- 99.5–100.0: maximum 3 Units

If Intelligence does not explicitly request a Unit count, the conservative default is **1 Unit** for an otherwise eligible signal. AFIP does not automatically expand to 2 or 3 Units merely because the confidence ceiling permits them.

## Profile ceilings

- P1: capital-tier growth capped permanently at 0.10 lot per Unit.
- P2: capital-tier growth capped permanently at 1.00 lot per Unit.
- P3: capital-tier growth capped permanently at 10.00 lots per Unit.
- P4: fixed 0.01 lot per Unit, no lot-size growth, no total research Unit ceiling; each approved research entry remains subject to the normal safety gates and cooldown.

## Final allocation

`final units = min(intelligence request, confidence ceiling, balance slots, profile slots, risk capacity, margin capacity, trading-cost approval, execution capacity)`
