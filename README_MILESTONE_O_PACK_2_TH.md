# AFIP Milestone O Pack 2 — Learning Evidence Normalization

## วัตถุประสงค์
แปลง Learning Record แบบ immutable ที่ผ่าน Milestone O Pack 1 ให้เป็น Evidence Record มาตรฐานเดียวกันแบบ deterministic สำหรับงานวิจัย

## ข้อมูลที่ทำให้เป็นมาตรฐาน
- Dataset Role: TRAINING, EVALUATION หรือ HOLDOUT
- Outcome และ Direction
- Market Regime
- Confidence Score
- Realized R
- Maximum Favourable Excursion ในหน่วย R
- Maximum Adverse Excursion ในหน่วย R
- Cost Ratio
- Duration
- Sample Weight

## ขอบเขตความปลอดภัย
- ต้องมี Lineage จาก Pack 1 ที่ผ่านการยอมรับและเป็น immutable
- ต้องผ่าน Data Quality, ลำดับเวลา และ Future Safety
- ระงับค่าที่ไม่เป็นตัวเลขหรืออยู่นอกช่วงที่อนุญาต
- แยก Dataset Role อย่างชัดเจน
- ไม่อนุญาต Automatic Parameter Update
- ไม่เปลี่ยน Trading Logic
- ไม่เลื่อนข้อมูลเป็น Production Knowledge โดยอัตโนมัติ
- ไม่สร้าง Broker Request ไม่ส่ง Order และไม่แก้ Position
- Execution คงเป็น `LOCKED_SIMULATION_ONLY` และ `NO_ORDER_SENT`

## คำสั่งตรวจสอบ
```powershell
pytest tests/test_milestone_o_pack_2.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone O Pack 2 Learning Evidence Normalization"
git push
```
