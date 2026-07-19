# AFIP Phase U Pack 3.4.1

## การรับรองความพร้อมของชุดข้อมูลย้อนหลัง

Pack นี้เพิ่มระบบรับรองคุณภาพข้อมูล OHLC ย้อนหลังก่อนนำไปใช้กับการวิจัยแบบเดินหน้าตามลำดับเวลา

ระบบตรวจสอบ:

- การมีอยู่ของ M1, M5, M15, M30, H1, H4 และ D1
- ความถูกต้องของราคา Open, High, Low และ Close
- Timestamp ซ้ำและข้อมูลที่เรียงเวลาผิด
- ช่องว่างของข้อมูลและจำนวนแท่งที่คาดว่าขาด
- ระยะเวลาที่ข้อมูลครอบคลุม
- อัตราข้อมูลผิดปกติ ข้อมูลซ้ำ และข้อมูลขาด
- คะแนนคุณภาพและสิทธิ์ในการนำไปวิจัย

สถานะการรับรอง:

- `READY` — พร้อมใช้วิจัย
- `CAUTION` — ใช้ได้โดยต้องเก็บหลักฐานข้อจำกัดและตีความอย่างระมัดระวัง
- `QUARANTINED` — ห้ามนำเข้าสู่การจัดอันดับหรือการรับรองผลวิจัย

ระบบนี้ไม่เปลี่ยนนโยบาย P1–P4 ไม่เปลี่ยน Lot Size, SL, TP, Drawdown Limit หรือสิทธิ์ส่งคำสั่งซื้อขาย

## คำสั่งรับรองข้อมูลบน VPS

```powershell
python tools/afip_historical_dataset_certify.py `
  --input runtime\historical_data\gold_history.jsonl `
  --instrument GOLD# `
  --source-id XM_VPS_HISTORY `
  --output runtime\research\certification\historical_dataset_readiness.json
```

รองรับไฟล์ JSONL, JSON และ CSV โดยแต่ละรายการต้องมี timeframe, timestamp, open, high, low และ close
