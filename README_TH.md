# AFIP V1 Runtime Truth Contract Final

แพตช์นี้แก้ Regression เดียวที่เหลืออยู่: `broker_session_state` หายจาก Runtime Truth contract

การแก้ไข:
- คืน field `broker_session_state` เพื่อ Backward Compatibility
- PASSIVE process ที่ยังไม่มี active broker verification = `NOT_VERIFIED`
- terminal/process ที่หยุด = `DISCONNECTED`
- active verified connection = `CONNECTED`
- คง `session_state` รุ่นใหม่ไว้โดยไม่สร้าง Runtime Authority ซ้ำ
- ไม่แตะ Signal, Lot Authority, SL/TP, Risk Gate หรือ Execution Authority

วิธีใช้: แตก ZIP ที่อื่น แล้วคัดลอกทุกไฟล์ทับ `C:\AFIP` จากนั้นรันสคริปต์ที่ root ของโครงการ
