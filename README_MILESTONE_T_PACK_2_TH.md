# AFIP Milestone T Pack 2

## Chronological Replay & Position Management Research Foundation

Milestone T Pack 2 เพิ่มรากฐานวิจัยสำหรับจำลองกราฟย้อนหลังทีละแท่งตามเวลาอย่างเคร่งครัด โดยไม่เปิดเผยข้อมูลอนาคตให้จุดตัดสินใจ และใช้ศึกษาการบริหารตำแหน่งหลายทางเลือก

### สิ่งที่เพิ่ม

- จำลองแท่งเทียนตามลำดับเวลา
- No-Future-Data Decision Context
- รองรับแผนวิจัย 1, 2 หรือ 3 ไม้โดยไม่บังคับว่าต้องใช้ครบ
- บทบาทไม้ระยะสั้น ระยะกลาง ระยะยาว และ Dynamic
- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)
- ทางเลือก Hold, Close, Partial Close, Break-even, Trailing, Pyramid และ No-Pyramid
- Dynamic Pyramid Research Gate
- ป้องกันความเสี่ยงรวมเกินเพดาน
- ช่องติดตามราคาหลังปิด M30/H1/H4/D1
- Checksum แบบ Deterministic
- ผลวิจัยเริ่มต้นเป็น `EXPERIMENTAL`

### ขอบเขตความปลอดภัย

Pack นี้ไม่ส่งคำสั่ง MT5 ไม่แก้ตำแหน่ง Production ไม่เปลี่ยน Lot Size ไม่เปลี่ยน TP/SL และไม่เปลี่ยน Trading Logic ปัจจุบัน การถือข้ามวันเพียงอย่างเดียวไม่ให้สิทธิ์เพิ่มไม้ ระบบวิจัยพีระมิดต้องยืนยันว่าตำแหน่งมีกำไร ความเสี่ยงเดิมลดลง Market Regime และโครงสร้างยังสนับสนุน และความเสี่ยงรวมไม่เกินเพดาน

### การตรวจสอบ

```powershell
.\RUN_MILESTONE_T_PACK_2.ps1
```
