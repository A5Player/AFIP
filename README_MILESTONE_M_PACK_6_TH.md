# AFIP Milestone M Pack 6 — Pattern Validation

## วัตถุประสงค์
เพิ่มระบบตรวจสอบ Pattern และ Cluster จากสถิติการวิจัยแบบ Deterministic และตรวจสอบย้อนหลังได้

## ความสามารถ
- เกณฑ์จำนวนตัวอย่างขั้นต่ำ
- เกณฑ์ Expectancy ขั้นต่ำ
- เกณฑ์ Profit Factor ขั้นต่ำ
- เกณฑ์ R-Multiple Dispersion สูงสุด
- ผลตรวจแยกระดับ Pattern และ Cluster
- เหตุผลการปฏิเสธราย Scope
- ตรวจสอบ Statistics Lineage
- รหัสและลำดับผลแบบ Deterministic
- ป้องกัน Future Leakage
- จำกัดสิทธิ์ไว้เฉพาะ Research Knowledge
- Dashboard ภาษาอังกฤษและภาษาไทย

## ความปลอดภัย
- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- Base Unit: 0.01 lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: false
- Live Execution: disabled
- Order Status: NO_ORDER_SENT
- Production Knowledge Approval: false

ระบบนี้ไม่เปลี่ยน Trading Logic ไม่สร้าง Broker Request และไม่อนุญาตการส่งคำสั่งซื้อขาย

## การตรวจสอบ
```powershell
pytest tests/test_milestone_m_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## ขั้นต่อไป
Milestone M Pack 7 — Pattern Explainability
