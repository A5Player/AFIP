# AFIP Milestone O Pack 5 — Learning Stability Validation

## วัตถุประสงค์

ตรวจสอบเสถียรภาพของผลประเมิน Learning Performance จาก Pack 4 ข้ามช่วงเวลาวิจัยตามลำดับ โดยไม่ให้สิทธิ์ปรับ Parameter, เปลี่ยน Trading Logic, เลื่อน Production Knowledge หรือ Execution

## ขอบเขต

- ตรวจ Lineage และ ID ของ Performance Evaluation จาก Pack 4 ไม่ให้ซ้ำ
- บังคับลำดับเวลาของ Research Window และต้องมี EVALUATION หรือ HOLDOUT
- ตรวจ Data Quality, Future Safety, จำนวน Window ขั้นต่ำ และจำนวน Sample รวมขั้นต่ำ
- คำนวณค่าเฉลี่ย Evaluation Realized R, Population Standard Deviation, Generalization Gap เฉลี่ย/สูงสุด, Positive Window Rate และ Stable Window Rate แบบ deterministic
- ระงับเมื่อ Variability สูงเกิน, Generalization Gap เกินเพดาน, Positive Window ไม่เพียงพอ, Lineage ผิด หรือ Locked Policy ไม่ผ่าน

## ความปลอดภัย

Pack นี้ไม่มีสิทธิ์ปรับ Parameter, เปลี่ยน Trading Logic, เลื่อน Production Knowledge, แก้ Position, สร้าง Broker Request หรือส่ง Order

Execution ยังคง `LOCKED_SIMULATION_ONLY`, Direct Execution เป็น false, Live Execution ถูกปิด และ Order Status เป็น `NO_ORDER_SENT`
