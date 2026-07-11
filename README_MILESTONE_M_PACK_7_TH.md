# Milestone M Pack 7 — Pattern Explainability

เพิ่มระบบอธิบาย Pattern และ Cluster ที่ผ่านหรือไม่ผ่านการตรวจสอบแบบ Deterministic สำหรับงานวิจัยเท่านั้น

## ความสามารถ
- แสดงเหตุผลหลักและเหตุผลสนับสนุนที่ตรวจสอบย้อนหลังได้
- แสดง Risk Note อย่างชัดเจน
- จัดลำดับ Feature Contribution แบบคงที่
- รักษา Market Regime และ Source Lineage
- รายงานความครอบคลุมของคำอธิบาย
- ตรวจ Future Leakage, Data Quality, Broker, Symbol, Base Unit และ Execution Lock
- เพิ่ม Dashboard ภาษาอังกฤษและภาษาไทย

Production Knowledge Approval ยังปิดอยู่ และไม่มีการสร้าง Broker Request หรือส่งคำสั่งซื้อขาย

## คำสั่งตรวจสอบ
```powershell
pytest tests/test_milestone_m_pack_7.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

## Git
```powershell
git add .
git commit -m "Milestone M Pack 7 Pattern Explainability"
git push
```
