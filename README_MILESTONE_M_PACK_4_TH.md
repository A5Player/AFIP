# AFIP Milestone M Pack 4 — Pattern Clustering

## วัตถุประสงค์

Pack นี้เพิ่มระบบจัดกลุ่ม Pattern สำหรับการวิจัยแบบ Deterministic และแยกตาม Market Regime โดยใช้ Pattern ที่ผ่าน Pattern Knowledge Engine และ Pattern Similarity Search

## ขอบเขต

- แบ่ง Pattern ตาม Market Regime
- บังคับใช้ Feature Schema แบบ Canonical ภายใน Regime เดียวกัน
- สร้าง Similarity Graph และ Cluster แบบ Deterministic
- สร้าง Cluster ID แบบ Deterministic
- คำนวณ Centroid และ Average Internal Similarity ของแต่ละ Cluster
- รักษา Source Lineage ของทุก Cluster
- ตรวจ Duplicate Pattern ID, Schema Mismatch, Future Leakage และการละเมิด Safety Policy
- ผลลัพธ์ทั้งหมดเป็น Research-only

## ความปลอดภัย

- Broker: XM เท่านั้น
- Symbol: GOLD# เท่านั้น
- Base Unit: 0.01 lot
- Execution: `LOCKED_SIMULATION_ONLY`
- Direct Execution: ปิด
- Live Execution: ปิด
- Order Status: `NO_ORDER_SENT`
- Production Knowledge Approval: ปิด

## คำสั่งตรวจสอบ

```powershell
pytest tests/test_milestone_m_pack_4.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git

```powershell
git add .
git commit -m "Milestone M Pack 4 Pattern Clustering"
git push
```
