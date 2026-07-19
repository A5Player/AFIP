# Phase U Pack 3.3.6.1 — PowerShell Documentation Splatting Hotfix

แก้ `APPLY_PHASE_U_PACK_3_3_6_DOC_UPDATES.ps1` ซึ่งเดิมส่ง hashtable เข้า `Append-Once` แบบ positional argument ทำให้ PowerShell ถามค่า `Source` และหยุดรอรับข้อมูล

Hotfix นี้เปลี่ยนเป็น named-parameter splatting ที่ถูกต้อง:

```powershell
Append-Once @projectDatabaseAppend
Append-Once @handoffAppend
```

คุณสมบัติ:

- รันซ้ำได้
- ตรวจ marker ก่อน append
- ไม่เพิ่มเอกสารซ้ำ
- ไม่แก้ Python หรือ Trading/Execution/Risk policy
