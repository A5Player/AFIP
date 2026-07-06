"""Compatibility entrypoint for Production Milestone D Pack 1."""

from __future__ import annotations

from afip.runtime_wiring import RuntimeWiringRuntime


def build_runtime() -> RuntimeWiringRuntime:
    return RuntimeWiringRuntime()
