# AFIP Milestone L Pack 7 — Shadow Execution Observation

## วัตถุประสงค์
สังเกต Decision แบบ Paper ที่ผ่านการรับรองจาก Pack 6 เทียบกับสภาพตลาดและ Execution ปัจจุบัน โดยไม่สร้างหรือส่งคำขอไปยัง Broker

## ขอบเขต
- เชื่อมโยงการรับรองจาก Pack 6
- เชื่อมโยง Decision จาก Pack 3
- บันทึก Action และ Position State ที่ตั้งใจดำเนินการ
- ตรวจสอบโครงสร้างราคา BUY/SELL
- ตรวจสอบความสดของข้อมูลและสถานะตลาด
- ตรวจสอบ Spread และ Latency
- ตรวจสอบความเสี่ยง เวลา และ Market Structure
- บังคับใช้ Independent Trade Plan
- รวม Protected Runner ใน Exposure
- ปิด Traditional DCA และ Averaging Down
- สร้าง Shadow Observation ID แบบ Deterministic
- Dashboard Explainability ภาษาอังกฤษและภาษาไทย

## นโยบายความปลอดภัย
- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- 1 Unit = 0.01 Lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: False
- Live Execution: Disabled
- Order Status: NO_ORDER_SENT
- ไม่มีการสร้าง Broker Request
- ไม่มีการพยายามส่ง Order

## การตรวจสอบ
```powershell
pytest tests/test_milestone_l_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone L Pack 7 Shadow Execution Observation"
git push
```
