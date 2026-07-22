# AFIP V1 Final Process-Isolated MT5 Router Fix

แพตช์นี้แก้ปัญหา Router แบบ process เดียวสลับ P1-P4 แล้ว MetaTrader5 Python bridge ค้างที่ Terminal ล่าสุด เช่น P4 ส่งผลให้ P1-P3 ถูก BLOCK ด้วย `execution_ownership_mismatch_before_order_check` และ Router อาจปิดตัวแบบ native crash

สถาปัตยกรรมใหม่:

- Supervisor Router 1 process ซึ่งไม่ import MetaTrader5
- สร้าง child process อายุสั้นหนึ่งตัวต่อหนึ่ง Profile ต่อหนึ่ง cycle
- รอ child จบก่อนเริ่ม Profile ถัดไป
- ไม่มี profile worker ทำงานพร้อมกัน
- P1/P2/P3 ไม่แชร์ process-global MT5 session
- P4 ยังคง Research-only และแสดง `last_execution_* = NOT_APPLICABLE`

สถานะที่ถูกต้องหลัง Start:

- `router.mode = SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5`
- `router.pid` เป็นตัวเลข
- `router.running = true`
- `router.concurrent_profile_workers = 0`
- P1/P2/P3 มี `last_execution_*` ตรงกับ Profile ของตัวเองหลัง cycle
