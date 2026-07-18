# Milestone S Pack 7.1 — แก้ความหมายเพดาน Position ให้ถูกต้อง

Patch นี้ทำให้ Confidence และ Balance เป็น “เพดานสูงสุดที่อนุญาต” ไม่ใช่คำสั่งให้เปิดเต็มเพดานอัตโนมัติ

สาระสำคัญ:

- หาก Intelligence ไม่ระบุจำนวน Unit ระบบจะใช้ค่าอนุรักษ์นิยม 1 Unit
- Intelligence สามารถขอ 1, 2 หรือ 3 Unit ได้ แต่จะถูกจำกัดด้วยเพดาน Confidence
- P1 เริ่ม 0.10 lot ต่อ Unit ที่ Balance 16,500 และไม่เกิน 0.10
- P2 เริ่ม 0.10 lot ต่อ Unit ที่ Balance 15,000 และเติบโตต่อจนถึงเพดาน 1.00
- P3 ใช้การเติบโตทุก 450 Balance ตามแผนจนถึงเพดาน 10.00
- P4 คงที่ 0.01 lot ต่อ Unit ไม่มีการเพิ่ม Lot และไม่จำกัดจำนวน Unit สะสมเพื่อ Research
- Gateway บันทึก requested Units, Confidence ceiling และเหตุผลการเลือกจำนวน Unit

Focused validation: 28 passed
Full regression จาก Repository ที่แนบมา: 2076 passed
