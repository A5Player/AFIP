# Milestone L Pack 6 — การรับรองผลงานแบบ Paper

Patch แบบเพิ่มเฉพาะส่วนนี้ทำหน้าที่รับรองค่าฐานจาก Paper Performance Analytics ของ Milestone L Pack 5

## ขอบเขต

- เชื่อมผลการวิเคราะห์จาก Pack 5
- รับรองจำนวนตัวอย่างขั้นต่ำ
- ตรวจเกณฑ์ Expectancy
- ตรวจเกณฑ์ Profit Factor
- ตรวจขีดจำกัด Drawdown
- ตรวจขีดจำกัดสัดส่วนต้นทุน
- ต้องมีกำไรสุทธิเป็นบวก
- รับรองคุณภาพข้อมูล
- ป้องกัน Future Leakage และข้อมูลไม่ครบ
- บังคับวงจร Position แบบอิสระ
- นับ Protected Runner ใน Exposure รวม
- ปิด Traditional DCA และ Averaging Down
- รับรองได้เฉพาะ Shadow Observation
- Demo และ Live Execution ยังปิดอยู่
- Dashboard อธิบายผลได้ทั้งอังกฤษและไทย

## นโยบายถาวร

- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- 1 Unit = 0.01 Lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: False
- Live Execution: Disabled
- Order Status: NO_ORDER_SENT

## การตรวจสอบ

```powershell
pytest tests/test_milestone_l_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git

```powershell
git add .
git commit -m "Milestone L Pack 6 Paper Performance Certification"
git push
```
