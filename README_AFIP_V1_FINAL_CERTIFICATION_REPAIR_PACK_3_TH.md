# AFIP V1 Final Certification Repair Pack 3

นโยบาย Authority ล่าสุด:

- P1: Capital Tier Table สูงสุด 3 ไม้ และสูงสุด 0.10 lot ต่อไม้
- P2: Capital Tier Table สูงสุด 3 ไม้ และสูงสุด 1.00 lot ต่อไม้
- P3: Capital Tier Table สูงสุด 3 ไม้ และสูงสุด 10.00 lots ต่อไม้
- P4: 0.01 lot เพียง 1 ไม้ตลอด
- Confidence < 98.0 = 0 ไม้
- 98.0–98.49 = สูงสุด 1 ไม้
- 98.5–99.49 = สูงสุด 2 ไม้
- 99.5–100.0 = สูงสุด 3 ไม้

Capital Tier Table เป็น sizing authority เพียงตัวเดียวสำหรับ P1–P3 และ legacy capital-per-unit fields ไม่อยู่ใน config และไม่มีสิทธิ์คำนวณ lot.

## ติดตั้ง

```powershell
cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_FINAL_CERTIFICATION_REPAIR_PACK_3.ps1 -ProjectRoot C:\AFIP\source
```

## ทดสอบ

```powershell
.\RUN_AFIP_V1_FINAL_CERTIFICATION_REPAIR_PACK_3.ps1 -ProjectRoot C:\AFIP\source
.\.venv\Scripts\python.exe -m pytest -q
```
