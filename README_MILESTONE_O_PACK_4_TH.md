# AFIP Milestone O Pack 4 — Learning Performance Evaluation

## วัตถุประสงค์

ประเมิน Aggregate จาก Pack 3 ที่ผ่านการยอมรับระหว่าง Dataset วิจัยที่แยกกัน โดยไม่ให้สิทธิ์ปรับระบบ เปลี่ยน Trading Logic เลื่อน Knowledge หรือ Execution

## ขอบเขต

- ตรวจ Lineage และ Aggregation Record ID ไม่ให้ซ้ำ
- ต้องมี Dataset ประเภท EVALUATION หรือ HOLDOUT
- ตรวจลำดับเวลา คุณภาพข้อมูล Future Safety จำนวนตัวอย่าง ความถูกต้องของค่าตัวเลข และนโยบาย Version 1.0 ที่ล็อกไว้
- คำนวณ Win/Loss/Breakeven Rate แบบถ่วงน้ำหนัก Confidence, Realized R, Total R, Payoff Ratio และ Generalization Gap ระหว่าง Training กับ Evaluation

## ความปลอดภัย

Pack นี้ไม่สามารถปรับ Parameter เปลี่ยน Trading Logic เลื่อนเป็น Production Knowledge แก้ Position สร้าง Broker Request หรือส่ง Order

Execution ยังคง `LOCKED_SIMULATION_ONLY`, Direct Execution เป็น false, Live Execution ถูกปิด และ Order Status คือ `NO_ORDER_SENT`
