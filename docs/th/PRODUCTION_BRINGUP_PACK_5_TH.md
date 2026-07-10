# Production Bring-up Pack 5 — ศูนย์คำสั่งแบบอธิบายได้

## วัตถุประสงค์

Pack 5 เพิ่ม Explainable Order Center แบบอ่านอย่างเดียวให้กับ AFIP Dashboard เพื่อให้ระบบไม่เป็น Black Box และสามารถอธิบายเหตุผลของคำสั่งจำลองทุกจุดเป็นภาษาอังกฤษและภาษาไทยได้

## ขอบเขตงาน

Patch นี้เพิ่มการแสดงเหตุผลสำหรับ:

- เหตุผลที่รอ
- เหตุผลการเข้าเทรด
- เหตุผลการถือสถานะ
- เหตุผลการเลื่อน Stop Loss
- เหตุผลการปรับ Take Profit
- เหตุผล Trailing Stop
- เหตุผลการปิดบางส่วน
- เหตุผลการออกจากสถานะ
- การกระทำถัดไปที่คาดไว้
- ความมั่นใจ
- ความเสี่ยง
- เวลาตรวจสอบครั้งถัดไป

## นโยบายความปลอดภัย

- Live execution ยังปิดอยู่
- Broker ยังจำกัดเฉพาะ XM
- Symbol ยังจำกัดเฉพาะ GOLD#
- ระบบ Unit ยังเป็น 1 Unit = 0.01 Lot
- ห้ามเพิ่ม Lot โดยตรง ระบบแสดงเฉพาะจำนวน Unit และ Total Lot ที่คำนวณจาก Unit
- โมดูลนี้อ่านข้อมูลอย่างเดียวและไม่ส่งคำสั่งไปยัง Broker
- ไม่เปลี่ยน Trading Logic เดิม

## Runtime

Runtime ใหม่:

```text
afip.explainable_order_center.ExplainableOrderCenterRuntime
```

Runtime นี้รับข้อมูล Dashboard และ Paper Order เดิม แล้วแปลงเป็นรายงานเหตุผลสองภาษาแบบ deterministic หาก Broker ไม่ใช่ XM, Symbol ไม่ใช่ GOLD#, หรือมีการเปิด Live Execution ระบบจะบล็อกในชั้น Explainability ทันที

## การเชื่อมกับ Dashboard

Dashboard เพิ่ม Panel ใหม่:

```text
Explainable Order Center / ศูนย์คำสั่งแบบอธิบายได้
```

Panel นี้แสดงสถานะคำสั่ง จำนวน Unit, Total Lot, Confidence, Risk, Next Action, Next Review Time และเหตุผลสองภาษาสำหรับการบริหารคำสั่งทุกจุดสำคัญ

## ความเข้ากันได้ย้อนหลัง

Patch นี้รองรับโครงสร้างเดิมทั้งหมด โดยเพิ่มโมดูลใหม่และ Panel ใหม่เท่านั้น ไม่แทนที่ Paper Trading, Decision, Execution หรือ Market Calendar เดิม

## การตรวจสอบ

รันคำสั่ง:

```powershell
pytest tests/test_production_bringup_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

ผลที่คาดหวัง:

```text
Production Bring-up Pack 5: PASS
Live execution: disabled
Dashboard: generated
```
