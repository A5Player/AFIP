# AFIP V1 Final Pack — Runtime Observatory & Historical Research Completion

Patch ชุดสุดท้ายสำหรับ AFIP V1 เพื่อให้ Historical Loading, Historical Replay และ Continuous Research แสดงสถานะจริงแบบสด โดยไม่เพิ่มอำนาจการเปิดออเดอร์

## สิ่งที่เพิ่มและแก้ไข

- Runtime Progress Authority เดียวที่ `runtime/research/runtime_observatory_status.json`
- Live Timeline แบบ append-only ที่ `runtime/research/runtime_observatory_timeline.jsonl`
- Replay อัปเดตทุกแท่ง: timeframe, index, processed/total, %, speed, ETA, heartbeat และ candle timestamp
- แยกสถานะ `RUNNING`, `WAITING`, `STALLED`, `COMPLETED`, `FAILED`
- Dashboard 4 อ่านสถานะจริงจาก authority นี้ก่อนแหล่ง legacy
- Layout กะทัดรัดสำหรับหน้าจอ 1080p
- ลบการแสดงผล compatibility แบบ `Capital / 0.01`
- Live Execution ไม่ถูก arm อัตโนมัติและยังต้องได้รับอนุญาตจากผู้ใช้โดยตรง

## ความปลอดภัย

Observatory เป็น read-only, ไม่มี execution authority, ไม่เรียก order send และไม่แก้ logic การเปิดออเดอร์
