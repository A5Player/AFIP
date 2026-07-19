# AFIP Phase U Final Integration

ชุดนี้เพิ่มตัวควบคุมการวิจัยแบบครั้งเดียวที่มีเวลาสูงสุดชัดเจน ป้องกัน MT5 หรือผู้ให้บริการข้อมูลค้างจน PowerShell ไม่จบ และสร้างรายงานตรวจสอบย้อนหลังได้

## วิธีรัน

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_AFIP_FINAL_RESEARCH.ps1
```

ค่ามาตรฐาน:
- Collector สูงสุด 900 วินาที
- Dashboard สูงสุด 180 วินาที

ปรับเวลาได้ เช่น:

```powershell
.\RUN_AFIP_FINAL_RESEARCH.ps1 -CollectorTimeoutSeconds 1200
```

ระบบยังเป็น Research-only และไม่มีสิทธิ์เปิดออเดอร์
