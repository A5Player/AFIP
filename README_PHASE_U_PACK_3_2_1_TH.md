# AFIP Phase U Pack 3.2.1

แพตช์แก้ปัญหา Research Startup ดูเหมือนค้างหลังจบ Tests โดยเพิ่มสถานะและความคืบหน้าที่มองเห็นได้ตลอด Pipeline

ลำดับการทำงาน:
1. Regression Tests
2. ตรวจไฟล์วิจัยและ Historical Data เดิม
3. โหลดแท่งปิดจาก MT5 เมื่อ OHLC ไม่เพียงพอ
4. Replay แยกตาม Timeframe โดยเรียงตามเวลา
5. บันทึก Dataset/Status
6. สร้าง Dashboard 1-3 ใหม่
7. เปิด Dashboard 3

ทุกขั้นใช้ Read-only Research Authority เท่านั้น ไม่มี order_check หรือ order_send

รัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_2_1.ps1
```
