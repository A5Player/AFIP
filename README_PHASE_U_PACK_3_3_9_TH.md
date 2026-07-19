# AFIP Phase U Pack 3.3.9

## Historical Readiness Compatibility Hotfix

แก้ Regression หลังเพิ่ม M30 เข้า Universal Timeframe Registry

ปัญหาเดิม:
- `DEFAULT_TIMEFRAMES` เพิ่มจาก 6 เป็น 7
- Historical readiness ใช้จำนวน Timeframe ทั้งหมดคูณหา `expected_bars`
- Test และสัญญาเดิมที่มี M1, M5, M15, H1, H4, D1 จึงถูกลดจาก READY เป็น REVIEW
- Dashboard Intelligence จึงเปลี่ยนจาก READY เป็น WAITING ตาม Dependency

แนวทางแก้:
- M30 ยังคงเป็น Timeframe ที่รองรับเต็มรูปแบบ
- สัญญา Legacy readiness ยังใช้ Core 6 timeframes:
  M1, M5, M15, H1, H4, D1
- `expected_bars` ของ readiness เดิมคำนวณจาก Core 6
- M30 เป็น enrichment timeframe และไม่ทำให้ข้อมูลเดิมถูกลดสถานะ
- ไม่แก้ Trading Logic
- ไม่เปิด Execution
- ไม่ลด Data Quality gate สำหรับ missing/duplicate/invalid bars

## การติดตั้ง

แตก ZIP แล้วนำไฟล์ทั้งหมดไปทับ Repository เดิม จากนั้นรัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_3_9.ps1
```
