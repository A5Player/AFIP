# คู่มือปฏิบัติการ AFIP Financial Data Lake

Financial Data Lake เป็นฐานข้อมูลกลางสำหรับงานวิจัย ไม่ผูกข้อมูลหลักติดกับ P1-P4 และไม่มีสิทธิ์ส่งคำสั่งซื้อขาย

ชั้นข้อมูลประกอบด้วย Raw, Normalized, Derived, Decision Context และ Outcome โดย Raw เป็นแบบ Append-only ห้ามแก้ทับ ข้อมูลคำนวณต้องมี Formula Version และข้อมูลที่เกี่ยวข้องกับการตัดสินใจต้องเชื่อม Decision Trace

ระบบแบ่ง Partition ตาม Layer, Domain, Instrument และวันที่ UTC พร้อม Record ID แบบ deterministic, SHA-256 และ Manifest เพื่อให้ตรวจสอบย้อนหลังได้

ข้อมูลจากเหตุขัดข้องหรือการตั้งค่าผิดยังเก็บไว้ แต่ต้องติดป้าย Quarantine หรือ Ineligible ห้ามนำไปฝึกหรือประเมินระบบโดยไม่ผ่านการรับรองใหม่
