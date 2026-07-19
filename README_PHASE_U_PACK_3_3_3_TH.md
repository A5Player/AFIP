# AFIP Phase U Pack 3.3.3 — M30 Chronological Replay & Coverage Evidence

## ขอบเขต

- คงการ Replay แบบเรียงลำดับเวลาของ M30 ผ่าน Timeframe Registry กลาง
- เพิ่มหลักฐาน Coverage แยกตาม Timeframe ใน `automatic_research_status.json`
- ผูก Replay Checkpoint กับตัวตนของช่วงข้อมูลที่ตรวจสอบได้แน่นอน
- ไม่ถือว่า Legacy Checkpoint ครอบคลุม MT5 Window ปัจจุบันโดยอัตโนมัติ
- Resume ต่อเมื่อ Timeframe, จำนวนแท่ง, เวลาแท่งแรก และเวลาแท่งสุดท้ายตรงกันทั้งหมด
- คง Append-only และ Deterministic Runtime
- ไม่แก้ Live Trading, Risk, Lot Size, Capital Gate, Maximum Units, SL, TP หรือ Order Execution

## ผลสอบสวน M5 2,000 → 1,441

ผลเดิมสอดคล้องกับการ Resume จาก Legacy Checkpoint ที่ตำแหน่ง 559 จึงเหลือประมวลผล 1,441 แท่งจากทั้งหมด 2,000 แท่ง แต่ Replay ID เดิมไม่ได้บันทึกขอบเขตเวลาแท่งแรกและแท่งสุดท้าย จึงไม่มีหลักฐานเพียงพอว่า 559 แท่งก่อนหน้านั้นเป็นข้อมูล Window เดียวกับที่โหลดล่าสุด

Pack 3.3.3 จึงไม่รับรอง Legacy Partial Checkpoint ว่าเป็น Coverage ที่สมบูรณ์ ระบบจะสร้าง Generation ID จาก Timeframe, จำนวนแท่ง, เวลาแท่งแรก และเวลาแท่งสุดท้าย แล้ว Replay Window นั้นตั้งแต่ index 0 ส่วนการรันครั้งถัดไปจะ Resume ได้เฉพาะ Window เดิมที่ตรงกันทุกค่า
