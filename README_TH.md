# AFIP V1 Runtime Certification Repair Pack 2

แพ็กซ่อมแบบ Patch Only สำหรับ 17 regression failures หลังติดตั้ง Control Center Pack 1

สิ่งที่แก้:
- คืน Router ให้ใช้ Authority เดิม: Sequential + short-lived child process + process-isolated MT5
- ลบ Architecture แบบ one-process-per-profile ที่ซ้ำและขัดกับ regression contract
- เพิ่ม import ของ `reclaim_stale_lock` จาก Production Runtime Authority เดิม
- แยก lock ของ injected MT5 test adapter ไปไว้ใน profile runtime เพื่อไม่ให้ pytest ชนกับ production lock ที่กำลังใช้งาน

แพ็กนี้ไม่แก้ Capital Gating, Lot, SL, TP, Confidence, Trading Cost หรือ Order Policy
