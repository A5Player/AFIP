"""Setup Wizard runtime for Milestone H Pack 3."""

from __future__ import annotations

from typing import Any, Mapping

from .wizard_report import SetupWizardReport, SetupWizardStep

_SAFE_EXECUTION_MODES = {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}


class SetupWizardRuntime:
    """Guide first setup while keeping execution locked to safe modes."""

    def evaluate_one(self, record: Mapping[str, Any]) -> SetupWizardReport:
        execution_mode = str(record.get("execution_mode", "LOCKED_SIMULATION_ONLY")).strip().upper()
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        login = str(record.get("login", "")).strip()
        password = str(record.get("password", "")).strip()
        mt5_path = str(record.get("mt5_terminal_path", record.get("mt5_path", ""))).strip()
        profile_name = str(record.get("profile_name", "Conservative")).strip() or "Conservative"
        history_ready = bool(record.get("history_ready", False))
        connection_test_passed = bool(record.get("connection_test_passed", False))
        saved = bool(record.get("saved", False))
        steps = (
            _step("welcome", "Welcome", "ยินดีต้อนรับ", True, "wizard_started"),
            _step("broker", "Broker", "โบรกเกอร์", broker == "XM" and symbol == "GOLD#", "xm_gold_policy_ready" if broker == "XM" and symbol == "GOLD#" else "version1_xm_gold_only_required"),
            _step("login", "Login", "เข้าสู่ระบบ", bool(login and password), "login_input_ready" if login and password else "login_input_required"),
            _step("mt5_path", "MT5 Path", "ตำแหน่งโปรแกรม MT5", bool(mt5_path), "mt5_path_ready" if mt5_path else "mt5_path_required"),
            _step("historical_data", "Download Historical Data", "ดาวน์โหลดข้อมูลย้อนหลัง", history_ready, "historical_data_ready" if history_ready else "historical_data_required"),
            _step("profile", "Profile Selection", "เลือกโปรไฟล์", bool(profile_name), "profile_selected" if profile_name else "profile_required"),
            _step("test_connection", "Test Connection", "ทดสอบการเชื่อมต่อ", connection_test_passed, "connection_test_passed" if connection_test_passed else "connection_test_required"),
            _step("save", "Save", "บันทึก", saved, "configuration_saved" if saved else "save_required"),
        )
        failed = tuple(step for step in steps if step.status != "READY")
        if execution_mode not in _SAFE_EXECUTION_MODES:
            return SetupWizardReport("BLOCKED", "live_execution_not_allowed_for_setup_wizard", "BLOCKED", steps, "safe_execution_mode", profile_name, broker, symbol, False, False)
        if failed:
            return SetupWizardReport("WAITING", "setup_wizard_incomplete", "WAITING", steps, failed[0].step_id, profile_name, broker, symbol, False, False)
        return SetupWizardReport("READY", "setup_wizard_ready", "SETUP_WIZARD_READY", steps, "run_afip", profile_name, broker, symbol, True, True)

    def explain_one(self, record: Mapping[str, Any]) -> SetupWizardReport:
        return self.evaluate_one(record)


def _step(step_id: str, name_en: str, name_th: str, ready: bool, reason: str) -> SetupWizardStep:
    return SetupWizardStep(step_id, name_en, name_th, "READY" if ready else "WAITING", reason)
