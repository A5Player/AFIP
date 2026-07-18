# AFIP Milestone S Cleanup Pack 4.1

## เป้าหมาย

แก้ไข Unit Allocation และ Protection Portfolio ให้ตรงตามนโยบายล่าสุด โดย `R` หมายถึง **Risk–Reward Ratio (RR)**

- Confidence 98.00–98.49: สูงสุด 1 Unit
- Confidence 98.50–99.49: สูงสุด 2 Units
- Confidence 99.50–100.00: สูงสุด 3 Units
- จำนวน Unit เป็นเพดาน ไม่ใช่คำสั่งให้เปิดครบ
- P1–P3 ใช้ Signal, Entry และเวลาเดียวกันได้
- Duplicate/Cooldown แยกตาม Profile และบัญชี
- แต่ละ Unit มี SL/TP และแผนดูแลกำไรของตนเอง

## บทบาท RR

- `RR_NEAR`: เป้าหมาย RR ใกล้ เพื่อเก็บกำไรส่วนแรก
- `RR_CORE`: เป้าหมาย RR หลัก
- `RR_RUNNER`: เป้าหมาย RR ไกลสำหรับแนวโน้มที่ยังแข็งแรง

เมื่อมี 1 หรือ 2 Units ระบบเลือกบทบาทตาม Market Regime และหลักฐาน ไม่บังคับเริ่มจาก RR_NEAR

## การตัดสินใจ SL/TP

ลำดับข้อมูล:

1. งานวิจัยที่ผ่านการตรวจและมี Sample อย่างน้อย 30
2. Structural Stop
3. ATR/Volatility
4. Realized Volatility จากข้อมูลราคา
5. Fallback ที่ติดป้าย `EVIDENCE_INSUFFICIENT_FALLBACK`

TP คำนวณจาก `Stop Distance × RR Target` และแต่ละ Unit เก็บค่า Break-even, Profit Lock, Trailing Start และ Maximum Giveback แยกกัน

## Balance Tier

P1: สูงสุด 0.10 lot ต่อ Order

P2: เพิ่มตามสูตรเดียวกับ P1 จนสูงสุด 1.00 lot ต่อ Order

P3: 0.02 ที่ Balance 900 แล้วเพิ่ม 0.01 ทุก Balance 450 จนสูงสุด 10.00 lot ต่อ Order

P4: 0.01 lot คงที่ ไม่มี Lot Growth และแยก Research Scenario/Protection Plan

## การรัน

แตก ZIP ทับโฟลเดอร์ AFIP แล้วรัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process Bypass -Force
.\RUN_MILESTONE_S_CLEANUP_PACK_4_1.ps1
```

Pack จะหยุด Demo Runner ก่อน Patch และจะไม่เปิดระบบกลับเอง
