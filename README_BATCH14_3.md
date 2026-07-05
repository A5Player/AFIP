# AFIP Production Batch 14.3 — Regression Fix

## วิธีใช้
แตกไฟล์ทับโฟลเดอร์ AFIP แล้วรัน:

```bash
python tools/afip_batch14_3_regression_fix.py
python tools/afip_local_quality_check.py
```

ถ้าผ่านแล้ว commit/push:

```bash
git add .
git commit -m "Production Batch 14.3: Stabilize local quality gate"
git push
```
