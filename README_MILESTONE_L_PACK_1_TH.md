# Milestone L Pack 1 — Paper Execution Foundation

เพิ่มรากฐานแบบกำหนดแน่นอนสำหรับการสังเกต Paper/Demo Execution ภายหลัง Milestone K ผ่านการรับรอง

## ขอบเขต
- ตรวจว่า Milestone K เสร็จสมบูรณ์
- ตรวจ Runtime Certification
- ตรวจการเชื่อมต่อบัญชี Paper
- ตรวจความพร้อมข้อมูลตลาดและข้อมูลย้อนหลัง
- ตรวจการตั้งค่าขีดจำกัดความเสี่ยง
- ตรวจ Audit และ Dashboard Explainability
- ตรวจนโยบาย XM เท่านั้น, GOLD# เท่านั้น และ 1 Unit = 0.01 lot
- ตรวจ Simulation Lock, การควบคุม Direct/Live Execution และ NO_ORDER_SENT
- สร้าง Foundation ID แบบ deterministic และคำอธิบาย Dashboard EN/TH

Pack นี้ไม่ส่ง แก้ไข หรือปิดคำสั่งซื้อขายจริง

## การตรวจสอบ
```powershell
pytest tests/test_milestone_l_pack_1.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
