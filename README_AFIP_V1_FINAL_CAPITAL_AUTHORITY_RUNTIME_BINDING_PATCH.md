# AFIP V1 Final Capital Authority Runtime Binding Patch

Purpose:
Bind Capital Authority decisions into the execution flow.

Target flow:

Signal
-> Confidence Authority
-> Capital Authority
-> Lot Authority
-> Risk Authority
-> Execution Gateway
-> MT5 Router

Rules:
- No fixed 0.01 x 3 execution bypass.
- No forced units.
- P1-P4 share the same execution pipeline.
- Profile differences are configuration based.
