# AFIP Milestone L Pack 8 — การรับรองการดำเนินการแบบ Demo

## วัตถุประสงค์
รับรองหลักฐาน Shadow Observation จาก Pack 7 ที่เรียงตามลำดับเวลา เพื่อเปิดความพร้อมสำหรับการสังเกตแบบ Demo ที่ควบคุมไว้ โดยยังไม่เปิดคำขอ Broker หรือการส่งคำสั่งซื้อขาย

## ขอบเขต
- ตรวจ Lineage จาก Performance Certification ของ Pack 6
- รวมและประเมิน Shadow Observation จาก Pack 7
- ตรวจจำนวนตัวอย่างขั้นต่ำ
- ตรวจอัตราความพร้อม อัตราผ่าน Spread และ Latency
- ตรวจข้อมูลตลาด Session ความเสี่ยง เวลา และโครงสร้างตลาด
- ตรวจลำดับเวลาและความไม่ซ้ำของ Observation ID
- บังคับใช้ Independent Trade Plan
- รวม Protected Runner ใน Exposure ทั้งหมด
- ห้าม Traditional DCA และ Averaging Down
- สร้าง Demo Certification ID แบบ Deterministic
- แสดงเหตุผลบน Dashboard ภาษาอังกฤษและภาษาไทย

## ขอบเขตการรับรอง
ผล READY หมายถึง `certified_for_demo_observation=True` เท่านั้น ไม่ได้เปิดการส่งคำสั่ง Demo หรือ Live และ `certified_for_demo_execution` ยังคงเป็น False จนกว่า Version 1.0 จะผ่าน Production Certification

## นโยบายความปลอดภัย
- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- 1 Unit = 0.01 Lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: False
- Live Execution: Disabled
- Order Status: NO_ORDER_SENT
- Broker Request Created: False
- Order Transmission Attempted: False

## คำสั่งตรวจสอบ
```powershell
pytest tests/test_milestone_l_pack_8.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone L Pack 8 Demo Execution Certification"
git push
```
