# Milestone S Pack 3 — ตัวจัดการการเชื่อมต่อ MT5 หลาย Terminal

เพิ่มการตรวจสุขภาพ MT5 แบบอ่านข้อมูลเท่านั้นและแยก P1–P4 โดยเชื่อมต่อทีละ Profile ด้วย terminal path, login และ server ของ Profile นั้น แล้ว shutdown session หลังตรวจทุกครั้ง ตรวจไฟล์ Terminal, การยืนยันบัญชี, Account/Server ตรงกัน, GOLD#, Tick และสถานะ Connected พร้อมบันทึก `runtime/profiles/pN/mt5_health.json` ให้ Dashboard อ่าน

ไม่มีการเรียก API ส่ง Order ระบบยังเป็น `LOCKED_SIMULATION_ONLY`, direct/live execution เป็น false และ `NO_ORDER_SENT`
