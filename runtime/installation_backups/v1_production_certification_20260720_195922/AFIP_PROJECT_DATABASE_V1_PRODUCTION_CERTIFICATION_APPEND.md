## AFIP V1 Production Certification

Added a validation-only production certification authority after Final
Consolidation. The legacy financial naming validator is preserved and executed
inside a filtered temporary source mirror through an incremental fingerprint
cache. Runtime data and generated outputs are excluded from source validation.
Production readiness requires full regression PASS.
