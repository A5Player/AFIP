# AFIP V1 Production Certification

Pack นี้ปิดชั้น Validation ต่อจาก Final Consolidation โดยไม่เพิ่ม Trading Feature

## การแก้ปัญหาหลัก

- เก็บ validator เดิมไว้ที่ `tools/validate_financial_naming_legacy.py`
- เปลี่ยน entry point เดิมให้เป็น incremental wrapper
- ไม่สแกน `runtime`, dashboard ที่ generate แล้ว, backup, cache และ `.venv`
- ตรวจใน temporary source mirror
- cache ผล PASS ตาม repository fingerprint
- มี timeout ป้องกันค้าง
- รวม targeted tests, architecture, dashboard, financial naming,
  local quality และ full regression ไว้ใน runner เดียว

## รันแบบตรวจชุดหลัก

```powershell
.\RUN_AFIP_V1_PRODUCTION_CERTIFICATION.ps1
```

## รัน Full Regression เพื่อรับ Production Certificate

```powershell
.\RUN_AFIP_V1_PRODUCTION_CERTIFICATION.ps1 -FullRegression
```

## รวม MT5 Operational Check

```powershell
.\RUN_AFIP_V1_PRODUCTION_CERTIFICATION.ps1 -FullRegression -Mt5Check
```

รายงานอยู่ที่:

`runtime\certification\production_certification.json`
