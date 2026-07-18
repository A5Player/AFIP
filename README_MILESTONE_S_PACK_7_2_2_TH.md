# AFIP Milestone S Pack 7.2.2 - P2 Position Limit Validation

แพตช์แก้ไขนี้คง AFIP Position Policy V2.1 และตรวจสอบเพดานขนาดสถานะของ P2 ให้ชัดเจน

นโยบายที่ยืนยัน:

- P1 มี lot สูงสุดต่อคำสั่ง 0.10
- P2 มี lot สูงสุดต่อคำสั่ง 1.00
- P3 มี lot สูงสุดต่อคำสั่ง 10.00
- P4 ใช้ lot วิจัยคงที่ 0.01
- Capital tier สุดท้ายของ P2 คือ minimum balance 1,545,300 และเปิดสาม Units ที่ 1.00 lot
- Capital tier ของ P2 ต้องไม่มีค่า lot สูงกว่า 1.00
- ค่า 1.01 ถึง 10.00 เป็น Capital tier ของ P3 เท่านั้น

ลำดับการใช้งาน:

```powershell
.\APPLY_MILESTONE_S_PACK_7_2_2.ps1
.\RUN_MILESTONE_S_PACK_7_2_2.ps1
python -m pytest -q
python tools/afip_local_quality_check.py
```

ยังไม่ควร Commit จนกว่า Full Regression และ AFIP Local Quality Check จะผ่านทั้งหมด
