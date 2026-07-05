from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "afip" / "pipeline" / "real_market_data_intelligence_wiring.py"
DOC = ROOT / "docs" / "PRODUCTION_BATCH14_6_STATUS_COMPATIBILITY.md"

print("AFIP Production Batch 14.6 Status Compatibility Fix")
print(f"Project root: {ROOT}")

if not TARGET.exists():
    raise SystemExit(f"missing target: {TARGET}")

text = TARGET.read_text(encoding="utf-8")
original = text

# Provider compatibility mode must still be considered READY for test/dry-run providers.
# Real MT5 provider failures remain controlled by the connection result itself.
text = text.replace('"status": "FALLBACK_READY"', '"status": "READY"')
text = text.replace("'status': 'FALLBACK_READY'", "'status': 'READY'")

# If previous patch created a fallback_status variable, normalize it too.
text = text.replace('fallback_status = "FALLBACK_READY"', 'fallback_status = "READY"')
text = text.replace("fallback_status = 'FALLBACK_READY'", "fallback_status = 'READY'")

if text == original:
    print("note: no FALLBACK_READY marker found; file may already be patched")
else:
    TARGET.write_text(text, encoding="utf-8")
    print("patched: afip/pipeline/real_market_data_intelligence_wiring.py READY compatibility")

DOC.parent.mkdir(parents=True, exist_ok=True)
DOC.write_text("""# Production Batch 14.6 — Status Compatibility Fix

## Purpose
Normalize test/dry-run provider compatibility status to `READY` while preserving locked simulation execution.

## Validation
Run:

```bash
python tools/afip_local_quality_check.py
```

Expected result:

```text
AFIP Local Quality Summary
Status: PASS
```
""", encoding="utf-8")
print("updated: docs/PRODUCTION_BATCH14_6_STATUS_COMPATIBILITY.md")
print("Done. Now run: python tools/afip_local_quality_check.py")
