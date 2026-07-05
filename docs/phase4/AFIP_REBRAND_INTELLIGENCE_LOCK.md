# AFIP Rebrand + Intelligence Naming Lock

Official product name:

**AFIP — Automated Financial Intelligence Platform**

## Naming policy

AFIP ใหม่ต้องใช้ชื่อซอฟต์แวร์การเงินสากลเท่านั้น และตัดคำ/ชื่อที่ให้ภาพแบบทหารออกจากแกนระบบ เอกสาร และโค้ดใหม่ทั้งหมด

## Intelligence-first terminology

คำว่า `Engine` ถูกจัดเป็นคำ legacy/compatibility สำหรับไฟล์เก่าที่ต้องคงไว้ชั่วคราวเท่านั้น โค้ดใหม่ต้องใช้คำว่า `Intelligence` เช่น

- Decision Intelligence
- Execution Intelligence
- Risk Intelligence
- Portfolio Intelligence
- Market Intelligence
- Position Intelligence
- Strategy Intelligence
- News Intelligence
- Time Intelligence
- Research Intelligence

## Legacy execution naming blocked from new architecture

ห้ามใช้ชื่อเชิงทหาร/ยุทธวิธีใน AFIP ใหม่ทั้งหมด ให้ใช้ชื่อการเงินสากลและชื่อ Intelligence เท่านั้น

## Migration rule

- `python afip.py` คือ command ทางการใหม่
- `python aif.py` ยังใช้ได้ชั่วคราวเพื่อ compatibility เท่านั้น
- ไฟล์ compatibility wrapper ที่มีคำว่า `engine` ยังอาจอยู่ได้ระยะสั้น แต่ต้องไม่เป็นจุดพัฒนาใหม่
