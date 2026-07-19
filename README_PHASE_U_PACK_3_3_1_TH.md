# AFIP Phase U Pack 3.3.1 — Universal Timeframe Registry

แพตช์นี้สร้าง Timeframe Registry กลางแบบมีลำดับแน่นอน สำหรับ Historical Collection, Chronological Replay, Research, Gap Detection และ Dashboard

ลำดับ Timeframe หลังติดตั้ง:

`M1, M5, M15, M30, H1, H4, D1`

## สิ่งที่แก้ไข

- เพิ่ม `afip/timeframe_registry.py` เป็นแหล่งข้อมูล Timeframe กลาง
- เพิ่ม Metadata ของ M30 และการเชื่อมกับ `TIMEFRAME_M30` ของ MT5
- เชื่อม Automatic Research Collector และ Replay Loop เข้ากับ Registry
- เชื่อม Historical Download Pipeline เข้ากับ Registry
- รักษา API เดิมของ `TimeframeAdapter` และเอารายการ Timeframe ซ้ำออก
- ไม่เปลี่ยนนโยบาย Live Trading, Risk Threshold, Lot Sizing, SL, TP หรือ Execution Authority
- ไม่ลบและไม่เขียนทับ Historical/Research Data เดิม

## วิธีติดตั้งและตรวจสอบ

หยุด AFIP Runtime ที่อาจกำลังเขียนไฟล์ Research ก่อน แตก ZIP รวมที่โฟลเดอร์หลักของ AFIP แล้วรัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_3_1.ps1
```

กรณี M5 Replay 1,441 จาก 2,000 bars ยังเป็น Investigation ที่ต้องใช้หลักฐาน Pack นี้ไม่สรุปว่าเป็นพฤติกรรมปกติหรือเป็นข้อผิดพลาด
