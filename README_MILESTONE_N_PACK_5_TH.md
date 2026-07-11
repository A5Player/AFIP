# Milestone N Pack 5 — Portfolio Exposure Coordination

Patch แบบเพิ่มเฉพาะส่วนนี้ตรวจสอบ Exposure ของ Portfolio หลัง Milestone N Pack 4 Capital Allocation

ระบบประสานจำนวน Unit ฝั่ง BUY/SELL ความเสี่ยงรวม ความกระจุกตัวของทิศทาง และ Exposure ของ Protected Runner ระหว่าง Trade Plan ที่มีวงจรชีวิตแยกอิสระ การทำงานเป็น Deterministic และ Research-only ไม่มีสิทธิ์สร้างหรือส่งคำสั่งไปยัง Broker

## นโยบาย Production ที่ยังล็อกไว้

- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- Base Unit: 0.01 lot
- ห้าม Traditional DCA, Averaging Down, Martingale, Grid Trading และ Recovery Trading
- Execution คงเป็น `LOCKED_SIMULATION_ONLY`
- Direct Execution ปิดอยู่
- Order Status คงเป็น `NO_ORDER_SENT`

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_n_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git

```powershell
git add .
git commit -m "Milestone N Pack 5 Portfolio Exposure Coordination"
git push
```
