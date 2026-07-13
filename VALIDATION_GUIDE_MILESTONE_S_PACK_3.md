# Validation Guide — Milestone S Pack 3

1. Open and login each XM MT5 terminal at its assigned folder.
2. Run `RUN_MILESTONE_S_PACK_3.ps1`.
3. P1 and P4 must report `CONNECTED`; P2/P3 remain disabled unless selected and enabled.
4. If `BLOCKED`, verify terminal64.exe and environment credentials.
5. If `DEGRADED`, verify the displayed account/server and GOLD# in Market Watch.
6. If `DISCONNECTED`, open the matching terminal and check XM network/login status.
7. Confirm dashboard generation and `LOCKED_SIMULATION_ONLY / NO_ORDER_SENT`.
