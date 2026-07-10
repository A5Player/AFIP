"""Profile customization service; configuration only, never execution."""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping
from .models import CustomProfile, ProfileCustomizationReport, slugify
from .repository import ProfileRepository

_PRESETS = {
 "CONSERVATIVE": {"risk_level":"CONSERVATIVE","maximum_units":1,"capital_per_unit":150.0,"split_orders":True,"overnight_holding":False,"research_mode":False},
 "BALANCED": {"risk_level":"BALANCED","maximum_units":2,"capital_per_unit":120.0,"split_orders":True,"overnight_holding":False,"research_mode":False},
 "GROWTH": {"risk_level":"GROWTH","maximum_units":3,"capital_per_unit":100.0,"split_orders":True,"overnight_holding":True,"research_mode":False},
 "RESEARCH": {"risk_level":"RESEARCH","maximum_units":1,"capital_per_unit":100.0,"split_orders":True,"overnight_holding":False,"research_mode":True},
}

class ProfileCustomizationRuntime:
    def __init__(self, storage_path: str | Path = "runtime/profiles/profiles.json") -> None:
        self.repository = ProfileRepository(storage_path)

    def preview(self, record: Mapping[str, Any]) -> ProfileCustomizationReport:
        base = str(record.get("base_profile", "CUSTOM")).upper()
        profile = CustomProfile.from_mapping({**_PRESETS.get(base, {}), **dict(record), "base_profile": base})
        issues = []
        if len(profile.profile_name) < 2: issues.append("profile_name_too_short")
        if profile.maximum_units > 3 and profile.risk_level != "RESEARCH": issues.append("maximum_units_requires_research_review")
        if profile.capital_per_unit <= 0: issues.append("capital_per_unit_must_be_positive")
        if profile.archived and profile.active: issues.append("archived_profile_cannot_be_active")
        status = "REVIEW" if issues else "READY"
        return ProfileCustomizationReport(status, "Profile requires review." if issues else "Profile configuration is valid and ready to save.", "โปรไฟล์ต้องตรวจสอบเพิ่มเติม" if issues else "การตั้งค่าโปรไฟล์ถูกต้องและพร้อมบันทึก", profile, tuple(issues), "Correct validation items before saving." if issues else "Save, activate, duplicate, archive, or assign an account.", "แก้ไขรายการตรวจสอบก่อนบันทึก" if issues else "บันทึก เปิดใช้งาน คัดลอก เก็บถาวร หรือกำหนดบัญชีได้", False, False)

    def save(self, record: Mapping[str, Any]) -> ProfileCustomizationReport:
        report = self.preview(record)
        if report.validation_items: return report
        saved = self.repository.save(report.profile)
        return replace(report, profile=saved, reason_en="Profile saved with version history.", reason_th="บันทึกโปรไฟล์พร้อมประวัติเวอร์ชันแล้ว")

    def duplicate(self, profile_id: str, new_name: str) -> ProfileCustomizationReport:
        source = self.repository.get(profile_id)
        if source is None: return self.preview({"profile_name": new_name or "Custom Profile", "base_profile": "CUSTOM"})
        return self.save({**source.as_dict(), "profile_id": slugify(new_name), "profile_name": new_name, "active": False, "archived": False, "assigned_account_id": ""})

    def activate(self, profile_id: str) -> ProfileCustomizationReport:
        profile = self.repository.get(profile_id)
        if profile is None: return self.preview({"profile_name":"Missing Profile"})
        return self.save({**profile.as_dict(), "active": True, "archived": False})

    def archive(self, profile_id: str) -> ProfileCustomizationReport:
        profile = self.repository.get(profile_id)
        if profile is None: return self.preview({"profile_name":"Missing Profile"})
        return self.save({**profile.as_dict(), "active": False, "archived": True})

    def assign_account(self, profile_id: str, account_id: str) -> ProfileCustomizationReport:
        profile = self.repository.get(profile_id)
        if profile is None: return self.preview({"profile_name":"Missing Profile"})
        return self.save({**profile.as_dict(), "assigned_account_id": str(account_id).strip()})
