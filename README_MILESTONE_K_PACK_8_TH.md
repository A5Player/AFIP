# AFIP Milestone K Pack 8 — Execution Supervisor

เพิ่มระบบควบคุมกลางแบบ Deterministic สำหรับเลือกคำแนะนำ Paper/Demo ที่ผ่านการตรวจและมีลำดับความสำคัญสูงสุดเพียงหนึ่งรายการ

## ขอบเขต
- ตรวจจับ Action ที่ขัดแย้งกันและตัดสินตามลำดับความสำคัญด้านการเงิน
- ควบคุม ENTRY, HOLD, STOP LOSS, TAKE PROFIT, TRAILING STOP, PARTIAL CLOSE และ EXIT
- ตรวจสถานะ Position, Fixed Unit, ความเสี่ยง, เวลา, ต้นทุน, Market Structure, Market Regime และ Dependency Reports
- แสดงเหตุผลภาษาอังกฤษและภาษาไทย
- เพิ่มแผง Execution Supervisor ใน Dashboard

## นโยบายความปลอดภัย
- XM เท่านั้น
- GOLD# เท่านั้น
- 1 Unit = 0.01 lot
- LOCKED_SIMULATION_ONLY
- ปิด Direct Execution
- ปิด Live Execution
- NO_ORDER_SENT

## การตรวจสอบ
```powershell
pytest tests/test_milestone_k_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
