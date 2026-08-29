"""
config/personas.py
Defines the enterprise personas for EDITH:
- executive: Executive / CRO (company-wide, condensed narrative depth, high-level decisions)
- regional_lead: Regional Sales Lead, Region B (operational framing with role-based data security restrictions)
- analyst: Analyst / RevOps (full unconstrained analytical depth, all hypotheses, all regions)
"""
from typing import Dict, List, Any, Optional

PERSONAS: Dict[str, Dict[str, Any]] = {
    "executive": {
        "id": "executive",
        "name": "Executive / CRO",
        "role_title": "Chief Revenue Officer",
        "depth": "condensed",
        "scope": "company_wide",
        "target_region": None,
        "badge_color": "bg-[#F5E8FF] text-[#6F00B5] border-[#E9D5FF]",
        "description": "Company-wide strategic overview with condensed decision-oriented summaries.",
        "permissions": {
            "view_company_wide": True,
            "view_all_regions": True,
            "view_competitor_intelligence": True,
            "view_all_hypotheses": True,
            "control_pricing_levers": True,
            "view_lineage": True
        }
    },
    "regional_lead": {
        "id": "regional_lead",
        "name": "Regional Sales Lead (Region B)",
        "role_title": "Regional Sales Director - Region B",
        "depth": "operational",
        "scope": "region_b",
        "target_region": "Region B",
        "badge_color": "bg-[#FFF8E1] text-[#A15C00] border-[#FFE082]",
        "description": "Operational view scoped to Region B with restricted access to company-wide aggregates and competitor intelligence.",
        "permissions": {
            "view_company_wide": False,
            "view_all_regions": False,
            "view_competitor_intelligence": False,
            "view_all_hypotheses": True,
            "control_pricing_levers": False,
            "view_lineage": False
        },
        "restricted_sections": [
            "company_wide_aggregates",
            "cross_region_breakdowns",
            "competitor_intelligence",
            "cross_region_control_groups",
            "pricing_rollback_lever"
        ]
    },
    "analyst": {
        "id": "analyst",
        "name": "Analyst / RevOps",
        "role_title": "Senior Revenue Operations Analyst",
        "depth": "full",
        "scope": "company_wide",
        "target_region": None,
        "badge_color": "bg-[#EDF7ED] text-[#16803C] border-[#C8E6C9]",
        "description": "Unrestricted analytical workbench with full multi-hypothesis ledgers, cross-region telemetry, and data lineage.",
        "permissions": {
            "view_company_wide": True,
            "view_all_regions": True,
            "view_competitor_intelligence": True,
            "view_all_hypotheses": True,
            "control_pricing_levers": True,
            "view_lineage": True
        }
    }
}

DEFAULT_PERSONA = "executive"

def get_personas() -> List[Dict[str, Any]]:
    """Returns list of all available persona definitions."""
    return list(PERSONAS.values())

def get_persona(persona_id: Optional[str]) -> Dict[str, Any]:
    """Retrieves a persona definition by id, defaulting to 'executive' if unrecognized."""
    if not persona_id:
        return PERSONAS[DEFAULT_PERSONA]
    clean_id = str(persona_id).lower().strip()
    return PERSONAS.get(clean_id, PERSONAS[DEFAULT_PERSONA])
