# AFIP Phase U Pack 3.2.2

แก้ `ValueError: replay resume index exceeds available candle count`

สาเหตุ: checkpoint เดิมมี replay index มากกว่าจำนวนแท่งใน MT5 window รอบปัจจุบัน

แนวทางแก้:
- ตรวจ checkpoint ก่อน replay ทุก timeframe
- หาก checkpoint เก่าเกินข้อมูลปัจจุบัน ให้เริ่ม generation ใหม่ด้วย window identity
- ไม่ลบ ไม่แก้ และไม่เขียนทับ research history เดิม
- ยังคง append-only และ chronological replay
- แสดงข้อความ stale checkpoint และ generation ที่เริ่มใหม่ใน PowerShell

ติดตั้งโดยแตก ZIP รวมลง C:\AFIP แล้วรัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_2_2.ps1
```
