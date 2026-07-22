# AFIP Phase U Pack 3.6 — Dashboard Authority Consolidation

Pack นี้รวมการสั่งสร้าง Dashboard ทั้งชุดไว้ที่ `DashboardAuthority` เพียงจุดเดียว ขณะที่ API เดิมยังคงใช้งานได้ผ่าน adapter ใน launcher

## การปรับ UI
- ลดขนาดไอคอนเมนูและไอคอนตาราง
- ลดหัวข้อและข้อความที่ใหญ่เกินไป
- บังคับหัวข้อเมนู/หัวข้อ panel สำคัญให้อยู่หนึ่งบรรทัดเมื่อพื้นที่พอ
- ใช้ ellipsis เมื่อข้อความยาว เพื่อไม่ให้ layout แตก
- ลดความกว้างคอลัมน์ metric และปรับ cell typography ให้เป็นระเบียบ

## Safety
- ไม่เริ่ม execution
- ไม่เริ่ม research อัตโนมัติ
- ไม่แก้ MT5, broker, credentials, SL/TP, lot authority หรือ safety gates
