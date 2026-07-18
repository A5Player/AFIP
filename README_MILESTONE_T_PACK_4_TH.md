# AFIP Milestone T Pack 4

## ระบบวิจัยการออกจากสถานะ การควบคุมขาดทุน และผลลัพธ์ของสถานะ

Pack 4 เพิ่ม Engine สำหรับงานวิจัยเท่านั้น เพื่อทดลองนโยบาย Exit และ Position Management หลายแบบบนกราฟ Replay ที่เดินตามลำดับเวลา ทุกผลลัพธ์ยังเป็น `EXPERIMENTAL` เก็บแบบ append-only และถูกกักกันไม่ให้ Production Runtime ใช้งาน

## สิ่งที่เพิ่ม

- Exit Research Engine
- Loss-Control Research
- Dynamic TP Research
- Dynamic SL Research
- Break-even Research
- Trailing Stop Research
- Maximum Holding Period Research
- Position Lifecycle Dataset
- Position Outcome Classification
- Exit Quality Score
- Capital Preservation Score
- MFE / MAE
- Profit Capture, Missed Profit และ Avoided Loss
- Experiment Runner สำหรับเปรียบเทียบนโยบายหลายแบบ
- Research Dataset Expansion
- Research Quarantine Integration

## Dataset ใหม่

- `position_lifecycles`
- `exit_alternatives`
- `position_outcomes`
- `exit_quality`

ข้อมูลทั้งหมดเชื่อม checksum chain ต่อจากโครงสร้าง append-only ของ Pack 3

## กติกา Replay แบบอนุรักษ์นิยม

ถ้าแท่งเดียวกันแตะทั้ง Stop และ Profit Target แต่ไม่ทราบลำดับการเคลื่อนไหวภายในแท่ง ระบบวิจัยจะถือว่า Stop ถูกแตะก่อน เพื่อป้องกันผลลัพธ์ที่มองโลกดีเกินจริงและลดความเสี่ยงของ future leakage

## ขอบเขตความปลอดภัย

Pack นี้ไม่ส่งคำสั่ง MT5 ไม่เปิด/แก้ไข/ปิดออเดอร์ ไม่เปลี่ยน TP, SL, Break-even, Trailing, Holding, Lot Size หรือ Production Trading Logic และไม่เลื่อนผลวิจัยเข้าสู่ Production Knowledge

## คำสั่งตรวจสอบ

```powershell
.\APPLY_MILESTONE_T_PACK_4_DOC_UPDATES.ps1
.\RUN_MILESTONE_T_PACK_4.ps1
python tools/validate_financial_naming.py
python tools/afip_local_quality_check.py
python -m pytest -q
```
