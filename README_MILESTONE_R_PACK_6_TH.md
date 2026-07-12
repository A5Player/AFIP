# Milestone R Pack 6 — Production Safety Audit

ตรวจสอบหลักฐานความปลอดภัยสำหรับ Production แบบ deterministic และ immutable หลัง Repository Cleanup

ขอบเขต: ตรวจ lineage จาก R Pack 5; ตรวจ Risk Boundary, Order Safety, Position Safety, Data Safety, Operational Safety และ Fail-safe; บังคับ ID ไม่ซ้ำ SHA-256 ลำดับเวลา การทบทวน ความครอบคลุมทุกโดเมน และ Safety Score; ระงับเมื่อพบความล้มเหลวหรือนโยบายล็อกถูกละเมิด

ใช้ namespace `afip.production_certification_safety_audit` เพื่อไม่ทับ Public API เดิม `afip.safety_audit`

Execution ยังคง `LOCKED_SIMULATION_ONLY`, ปิด Live/Direct Execution และ `NO_ORDER_SENT`

งานถัดไป: Milestone R Pack 7 — Security Audit
