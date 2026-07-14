# Milestone S Pack 4.1 — Live Dashboard Runtime Wiring

This stabilization patch makes the top of the AFIP dashboard operationally useful. P1-P4 cards show runtime state, MT5 connection, demo verification/arming, decision and confidence, waiting reason, order state, tickets, latency, last update, and freshness.

The dashboard service regenerates the HTML every five seconds. The browser also reloads every five seconds. No trading logic is changed.
