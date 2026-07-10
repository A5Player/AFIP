# Milestone L Pack 5 — การวิเคราะห์ผลงานแบบ Paper

## วัตถุประสงค์
รวมเฉพาะผลลัพธ์ Paper จาก Milestone L Pack 4 ที่ผ่านการรับรองเป็นสถิติผลงานแบบกำหนดแน่นอนและตรวจสอบย้อนหลังได้ โดยไม่เปลี่ยนกฎการซื้อขายและไม่ส่งคำสั่งซื้อขาย

## การวิเคราะห์ที่เพิ่ม
- จำนวนผลลัพธ์ที่มีสิทธิ์และถูกปฏิเสธ
- จำนวนชนะ แพ้ และเสมอตัว
- อัตราชนะ
- กำไรรวม ขาดทุนรวม และกำไรสุทธิ
- Profit Factor
- Average Realized R และ Expectancy R
- Maximum Drawdown จากผลลัพธ์สุทธิตามลำดับเวลา
- Trading Cost, Swap Cost และอัตราต้นทุนต่อกำไรรวม
- การตรวจจำนวนตัวอย่างขั้นต่ำ
- การคัดข้อมูลที่ใช้ข้อมูลอนาคตหรือข้อมูลไม่ครบออก
- การตรวจวงจร Position อิสระและ Exposure ของ Protected Runner
- คำอธิบาย Dashboard ภาษาอังกฤษและภาษาไทย

## นโยบายถาวร
- XM เท่านั้น
- GOLD# เท่านั้น
- 1 Unit = 0.01 lot
- ปิด Traditional DCA
- ปิด Averaging Down
- ปิด Martingale
- ปิด Grid Trading
- Protected Runner ยังต้องนับรวมใน Exposure และความเสี่ยงทั้งหมด
- LOCKED_SIMULATION_ONLY
- ปิด Direct Execution
- ปิด Live Execution
- NO_ORDER_SENT

## คำสั่งตรวจสอบ
```powershell
pytest tests/test_milestone_l_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone L Pack 5 Paper Performance Analytics"
git push
```
