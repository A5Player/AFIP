"""AFIP Connection Manager public API."""

from .connection_runtime import ConnectionManagerRuntime
from .connection_report import ConnectionManagerReport

__all__ = ["ConnectionManagerReport", "ConnectionManagerRuntime"]
