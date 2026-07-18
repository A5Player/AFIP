# AFIP Milestone S Pack 7.3 — สูตรกำหนดขนาดสถานะการลงทุนแบบ Deterministic

## วัตถุประสงค์

Patch นี้เปลี่ยนตาราง `capital_tiers` ขนาดใหญ่ของ P1-P3 ใน `config/four_profile_demo.json` ให้เป็นสูตรแบบย่อและคำนวณซ้ำได้แน่นอน ก่อนส่งข้อมูลเข้า Capital Growth Engine ระบบจะขยายสูตรกลับเป็นตารางในหน่วยความจำที่ให้ผลเหมือนเดิมทุกระดับ

## ความเข้ากันได้ของระบบ

- ยังคงใช้ `allocation_mode` เป็น `CAPITAL_TIER_TABLE`
- ไม่แก้ Capital Growth Engine
- ยังคงรองรับ `capital_tiers` แบบเดิม และให้ตารางเดิมมีลำดับความสำคัญสูงกว่าเมื่อมีอยู่
- P4 ยังคงเป็น `RESEARCH_FIXED_001`
- ไม่แก้ Entry, Confidence, TP, SL, Spread, Execution หรือการบริหารออเดอร์

## ขีดจำกัดเดิมที่คงไว้

- P1: 12 ระดับ สูงสุด `0.10 x 3` ที่ Balance `19,800`
- P2: 102 ระดับ สูงสุด `1.00 x 3` ที่ Balance `1,545,300`
- P3: 1,002 ระดับ สูงสุด `10.00 x 3` ที่ Balance `600,000`

## คำสั่งตรวจสอบ

```powershell
.\RUN_MILESTONE_S_PACK_7_3.ps1
python -m pytest -q
python tools/afip_local_quality_check.py
```
