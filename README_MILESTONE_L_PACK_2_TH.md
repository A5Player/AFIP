# Milestone L Pack 2 — ระบบติดตาม Paper Execution Session

เพิ่มการรับรองรอบการสังเกตแบบ Paper ต่อจากรากฐานใน Pack 1 โดยทำงานแบบกำหนดผลแน่นอน

## ขอบเขต
- ตรวจบัญชี Paper และช่วงเวลาตลาด
- ตรวจความสดใหม่ของข้อมูลตลาด
- ตรวจขีดจำกัด Spread และ Latency
- ตรวจการซิงก์เวลา
- ตรวจความเสี่ยงและ Audit
- บังคับ Independent Trade Plan
- ปิด Traditional DCA และการถัวขาดทุน
- XM เท่านั้น, GOLD# เท่านั้น, 1 Unit = 0.01 Lot
- คง LOCKED_SIMULATION_ONLY และ NO_ORDER_SENT
- Dashboard อธิบายเหตุผลภาษาอังกฤษและภาษาไทย

Pack นี้บันทึกเฉพาะความพร้อมและผลการสังเกต ไม่ส่ง แก้ไข หรือปิดคำสั่งกับ Broker

## การตรวจสอบ
```powershell
pytest tests/test_milestone_l_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
