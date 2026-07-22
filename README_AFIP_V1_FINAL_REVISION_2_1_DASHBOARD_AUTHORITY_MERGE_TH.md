# AFIP V1 Final Revision 2.1 — Dashboard Authority Merge

Patch Only สำหรับแก้ regression ที่ Revision 1 นำ Dashboard renderer เวอร์ชันเก่ามาทับ Single Runtime Progress Authority

การแก้ไข:
- Dashboard 4 อ่าน `runtime/research/runtime_observatory_status.json` ผ่าน `RuntimeProgressAuthority`
- แสดง replay percentage, processed bars, total bars, heartbeat และ timeframe จาก authority จริง
- คง `execution_authority=false` และ `order_send_called=false`
- ไม่เปลี่ยน replay engine, lot authority หรือ execution logic

ติดตั้งโดยแตก ZIP ทับ `C:\AFIP\source` แล้วรัน:

```powershell
.\RUN_AFIP_V1_FINAL_REVISION_2_1_DASHBOARD_AUTHORITY_MERGE.ps1
```
