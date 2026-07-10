# Milestone K Pack 7 — Partial Close Intelligence

## ขอบเขต
เพิ่มระบบตรวจสอบการปิดสถานะบางส่วนแบบ deterministic สำหรับ XM และ GOLD# ในโหมดจำลองเท่านั้น

## หลักควบคุม
- 1 Unit เท่ากับ 0.01 lot เสมอ
- การปิดบางส่วนต้องระบุเป็นจำนวน Unit เต็มเท่านั้น
- ต้องเหลือ Runner อย่างน้อยตามจำนวนขั้นต่ำที่กำหนด
- ตรวจทิศทางกำไรของ BUY และ SELL
- ต้องผ่านการตรวจผลกำไร ต้นทุน ความเสี่ยง เวลา และโครงสร้างตลาด
- Direct Execution และ Live Execution ยังคงปิด
- ผลลัพธ์ทุกครั้งยังเป็น `NO_ORDER_SENT` และ `LOCKED_SIMULATION_ONLY`

## Dashboard
เพิ่มคำอธิบาย EN/TH สำหรับความพร้อม จำนวน Unit ที่อนุมัติ Runner ที่เหลือ กำไรที่คาดว่าจะรับรู้ เหตุผลการถือ เหตุผล Partial Close ขั้นตอนถัดไป ความมั่นใจ และเวลาทบทวนครั้งถัดไป

## การตรวจสอบ
```powershell
pytest tests/test_milestone_k_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone K Pack 7 Partial Close Intelligence"
git push
```
