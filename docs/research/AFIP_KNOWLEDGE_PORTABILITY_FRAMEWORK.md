# AFIP Knowledge Portability, Recovery & Reuse Framework

Pack 6.3 makes research data portable without granting trading authority. A bundle contains `manifest.json` plus a `payload/` tree. Every file is identified by relative path, byte size, category, and SHA-256. Import defaults to verification only; applied imports are written into an isolated bundle-ID directory and never overwrite the source dataset.

Lifecycle: inventory -> manifest -> integrity verification -> export -> transfer -> verify-only import -> isolated recovery -> researcher review.

`execution_authority = NONE`; `promotion_to_execution = PROHIBITED`.
