# AFIP Milestone P Pack 7 — Market Behaviour Confidence Calibration

Patch นี้เพิ่มการปรับเทียบความเชื่อมั่นของพฤติกรรมตลาดแบบ Deterministic และ Research-only จากรายงาน Drift ของ Milestone P Pack 6 ที่ผ่านการตรวจแล้ว

## ขอบเขต

- ตรวจ Lineage และ Report ID ที่ไม่ซ้ำของ Pack 6
- ตรวจลำดับเวลา คุณภาพข้อมูล Future Safety และ Market Regime before Behaviour
- วัด Coverage ของ Transition Evidence
- ให้คะแนนเสถียรภาพของ Persistence, Regime Change, Behaviour Change และ Stable Window
- สร้าง Calibrated Confidence Score และ Confidence Band
- รักษา Immutable Record และ Execution Lock ของ Version 1.0

## ความปลอดภัย

Runtime นี้ไม่มีสิทธิ์ปรับ Parameter, เปลี่ยน Trading Logic, เลื่อนข้อมูลเป็น Production Knowledge, แก้ Position, สร้าง Broker Request หรือส่ง Order

Execution ยังคง `LOCKED_SIMULATION_ONLY`, Direct Execution เป็น False, Live Execution ปิด และ Order Status เป็น `NO_ORDER_SENT`
