"""AFIP Research Data Foundation.

Read-only research recording components. They never submit, modify, or close an
order and are deliberately isolated from the execution decision path.
"""
from .models import RESEARCH_CONTRACT_VERSION, ResearchEvent, TradeCase
from .recorder import ResearchRecorder, RecorderSummary

__all__ = [
    "RESEARCH_CONTRACT_VERSION",
    "ResearchEvent",
    "TradeCase",
    "ResearchRecorder",
    "RecorderSummary",
]
