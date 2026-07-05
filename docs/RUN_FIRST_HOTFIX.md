# AFIP Runtime V1 Hotfix

Problem:
`python afip.py` failed because `afip.py` shadowed the `afip/` package.

Fix:
The launcher now loads `afip/runtime/runtime_v1.py` by file path, so the command remains:

```powershell
python afip.py
```

Expected output:

```text
=== AFIP Runtime V1 ===
Status : OK
Mode   : SIMULATION
Workflow:
 - Load Configuration
 - Initialize Runtime
 - Load Intelligence
 - Load Strategies
 - Load Risk
 - Load Market Data
 - Generate Decision
 - Build Simulation Order
 - Generate Report
```
