# Phase U Pack 3.3.1.2 — PowerShell Marker Parsing Hotfix

แก้ข้อผิดพลาด `A positional parameter cannot be found that accepts argument 'Universal'` ในตัวอัปเดตเอกสาร

## การแก้ไข

- เปลี่ยนการส่ง parameter หลายบรรทัดแบบ backtick เป็น PowerShell parameter splatting
- ใช้ marker แบบ ASCII สั้นเพื่อหลีกเลี่ยงปัญหาการ parse และ encoding
- คงพฤติกรรม idempotent: เอกสารที่เคย append แล้วจะไม่ถูกเพิ่มซ้ำ
- ใช้ `IndexOf(..., Ordinal)` เพื่อรองรับ Windows PowerShell อย่างชัดเจน
- ไม่แก้ Python, trading policy, risk, lot sizing, SL, TP หรือ execution

## วิธีใช้

แตกไฟล์ลงทับ `C:\AFIP` แล้วรัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_3_1.ps1
```
