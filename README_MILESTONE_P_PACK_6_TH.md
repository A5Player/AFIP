# AFIP Milestone P Pack 6 — การตรวจ Drift ของพฤติกรรมตลาด

## วัตถุประสงค์

ตรวจความเปลี่ยนแปลงของพฤติกรรมตลาดระหว่างช่วง Baseline และ Recent แบบ deterministic โดยใช้รายงานเสถียรภาพที่ผ่าน Milestone P Pack 5

## ขอบเขต

ระบบเปรียบเทียบ:

- ค่าเฉลี่ย Persistence Ratio
- ค่าเฉลี่ยอัตราการเปลี่ยน Market Regime
- ค่าเฉลี่ยอัตราการเปลี่ยน Behaviour State
- Stable-window Rate
- ความครอบคลุมของ Transition
- Lineage จาก Pack 5
- ลำดับเวลาและ Future Safety

ผลลัพธ์เป็นรายงานวิจัยแบบ immutable เท่านั้น ไม่มีสิทธิ์ปรับ Parameter, Trading Logic, Position, Broker Request หรือ Order

## นโยบายถาวร

- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- Base Unit: 0.01 Lot
- Execution: LOCKED_SIMULATION_ONLY
- Direct Execution: ปิด
- Live Execution: ปิด
- Order Status: NO_ORDER_SENT

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_p_pack_6.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```
