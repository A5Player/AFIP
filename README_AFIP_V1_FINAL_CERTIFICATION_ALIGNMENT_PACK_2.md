# AFIP V1 Final Certification Alignment Pack 2

Final policy:
- P1-P4 are execution profiles.
- P4 is fixed at one 0.01-lot order.
- Research/replay does not require opening experimental orders.
- Process-isolated sequential router is the canonical MT5 ownership model.
- Injected simulation MT5 adapters bypass only the physical terminal-folder check; real MT5 retains exact login, server, terminal and request ownership checks.
- One lot authority remains the sizing authority.

Validation performed against AFIP(52).zip:
- Focused certification/regression set: 92 passed.
- Additional affected set: 85 passed.
- Full regression: 2636 passed.
