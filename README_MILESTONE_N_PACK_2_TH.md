# Milestone N Pack 2 — Adaptive Position Sizing

เพิ่มระบบคำนวณขนาด Position แบบ Deterministic สำหรับงานวิจัยเท่านั้น โดยใช้ทุน งบความเสี่ยง ระยะ Stop Loss ความสามารถด้าน Margin และ Confidence เพื่อแนะนำ 0–3 Unit แยกอิสระ Unit ละ 0.01 Lot ระบบไม่สร้างคำขอ Broker และไม่ส่งคำสั่งซื้อขาย

## ความปลอดภัย
- XM เท่านั้น
- GOLD# เท่านั้น
- 1 Unit = 0.01 Lot
- สูงสุด 3 Unit
- ต้องเป็น Independent Trade Plan
- รองรับ Protected Runner
- LOCKED_SIMULATION_ONLY
- NO_ORDER_SENT

## การตรวจสอบ
```powershell
pytest tests/test_milestone_n_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
