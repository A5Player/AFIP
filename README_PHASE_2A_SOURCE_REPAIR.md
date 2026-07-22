AFIP V1 Final Phase 2A Source Repair Patch

Modified:
- afip/demo_execution_gateway/runtime.py

Change:
- Legacy sizing fields are no longer rejected.
- Legacy fields are accepted only for backward compatibility.
- They cannot control lot sizing or unit allocation.
- Capital Authority remains the only sizing authority.

Install:
Copy afip/demo_execution_gateway/runtime.py over:
C:\AFIP\source\afip\demo_execution_gateway\runtime.py

Validate:
python -m pytest -q
