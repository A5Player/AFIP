# Milestone N Pack 4 — Capital Allocation

Adds a deterministic, research-only capital allocation runtime. It distributes only remaining portfolio risk, fixed 0.01-lot Units, and margin capacity among independent trade plans in priority order.

The runtime preserves the free-margin reserve, Portfolio Risk Engine lineage, protected-runner exposure, independent position lifecycles, and the permanent prohibition of Traditional DCA, Averaging Down, Martingale, Grid Trading, and Recovery Trading.

Execution remains `LOCKED_SIMULATION_ONLY`; direct execution and live execution remain disabled, and `NO_ORDER_SENT` is mandatory.
