from dataclasses import dataclass


@dataclass(frozen=True)
class ExitValidation:
    position_id: str
    symbol: str
    direction: str
    units: int
    recommended_action: str
    hold_allowed: bool
    partial_close_allowed: bool
    stop_loss_move_allowed: bool
    take_profit_change_allowed: bool
    trailing_stop_allowed: bool
    full_exit_allowed: bool
    approved_action: str
    action_approved: bool
    block_reasons: tuple[str, ...]
    explanation_en: str
    explanation_th: str


@dataclass(frozen=True)
class ExitValidationReport:
    status: str
    reason: str
    validations: tuple[ExitValidation, ...]
    selected_position_id: str
    approved_action: str
    approved_units: int
    holding_reason_en: str
    holding_reason_th: str
    stop_loss_move_reason_en: str
    stop_loss_move_reason_th: str
    take_profit_change_reason_en: str
    take_profit_change_reason_th: str
    trailing_stop_reason_en: str
    trailing_stop_reason_th: str
    partial_close_reason_en: str
    partial_close_reason_th: str
    exit_reason_en: str
    exit_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    next_review_time_utc: str
    direct_execution: bool = False
