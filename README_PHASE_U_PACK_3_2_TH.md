# AFIP Phase U Pack 3.2 — Automatic Research Runtime

แพตช์นี้เปิดใช้งานระบบวิจัยย้อนหลังที่มีอยู่จริงแบบอัตโนมัติทุกครั้งที่รัน `python afip.py simulate` หรือ `python -m afip.dashboard_ui`

หลักการสำคัญ:
- อ่านข้อมูล OHLC ที่หาได้จาก runtime/research, data/research, data/knowledge และ data/historical
- หากข้อมูลไม่พอ จะพยายามอ่านแท่งปิดจาก MT5 ที่เชื่อมต่ออยู่แบบ Read-only
- Replay ตามลำดับเวลา ไม่เปิดเผยข้อมูลอนาคต
- เขียน Dataset ใหม่แบบ append-only ที่ runtime/research/automatic/schema_v2
- ข้อมูลเก่าไม่ถูกลบ แต่สร้างใหม่ตาม Schema V2
- หลักฐานที่ขาดจะถูกบันทึกใน missing_evidence และไม่นำเข้า denominator ของคะแนน
- ไม่มี order_send, order_check หรือสิทธิ์ส่งคำสั่งซื้อขาย
- Dashboard 3 แสดงสถานะ จำนวนไฟล์ Records Bars Replay และนโยบายคะแนน
