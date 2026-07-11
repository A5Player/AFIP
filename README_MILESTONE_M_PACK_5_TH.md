# AFIP Milestone M Pack 5 — สถิติ Pattern

## วัตถุประสงค์

เพิ่มระบบสถิติสำหรับ Pattern รายตัวและ Pattern Cluster ที่มีผลลัพธ์แบบ Deterministic และตรวจสอบย้อนหลังได้

## ความสามารถ

- สถิติระดับ Pattern และ Cluster
- จำนวนตัวอย่าง จำนวนชนะ แพ้ เสมอ และ Win Rate
- Average R-Multiple และ Expectancy
- Gross Profit R, Gross Loss R และ Profit Factor
- ส่วนเบี่ยงเบนมาตรฐานของ R-Multiple
- ระดับความเชื่อมั่นของจำนวนตัวอย่างอย่างชัดเจน
- ตรวจลำดับเวลาของ Outcome
- ตรวจ Lineage ของ Pattern และ Cluster
- รหัสและลำดับสถิติแบบ Deterministic
- ป้องกัน Future Leakage
- ใช้สำหรับ Research Knowledge เท่านั้น
- เพิ่ม Dashboard ภาษาอังกฤษและภาษาไทย

## ความปลอดภัย

- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- Base Unit: 0.01 Lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: false
- Live Execution: ปิด
- Order Status: NO_ORDER_SENT
- Production Knowledge Approval: false

สถิติใน Pack นี้ไม่เปลี่ยนการตัดสินใจซื้อขาย และไม่อนุญาตให้สร้าง Broker Request หรือส่งคำสั่งซื้อขาย

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_m_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## ขั้นต่อไป

Milestone M Pack 6 — Pattern Validation
