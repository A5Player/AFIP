"""Central display-brand authority for AFIP Pro.

Internal package names, runtime paths, schema identifiers, and compatibility
entry points intentionally remain unchanged.
"""

PRODUCT_NAME = "AFIP Pro"
PRODUCT_SHORT_NAME = "AFIP"
CONTROL_CENTER_NAME = f"{PRODUCT_NAME} Control Center"
DASHBOARD_NAME = f"{PRODUCT_NAME} Dashboard"
RUNTIME_NAME = f"{PRODUCT_NAME} Runtime"
RESEARCH_NAME = f"{PRODUCT_NAME} Research"
PRODUCTION_CERTIFICATION_NAME = f"{PRODUCT_NAME} Production Certification"


def display_name(component: str | None = None) -> str:
    """Return the canonical product display name with an optional component."""
    component_text = str(component or "").strip()
    return PRODUCT_NAME if not component_text else f"{PRODUCT_NAME} {component_text}"
