"""
config/semantic_contracts.py
Governed KPI definitions, metric dependency definitions, dimension metadata, and candidate driver catalog.
"""
from typing import Dict, List, Any

# Governed KPI definitions
KPIS: Dict[str, Dict[str, Any]] = {
    "kpi_b2b_sales": {
        "id": "kpi_b2b_sales",
        "name": "Monthly B2B Sales",
        "category": "Revenue & Commercial",
        "unit": "$",
        "format": "${:,.0f}",
        "target": 1_250_000,
        "description": "Total monthly gross sales revenue from Enterprise and Mid-Market software contracts.",
        "primary_dimensions": ["region", "customer_tier", "product_line", "channel"],
        "source_systems": ["ERP Sales Ledger", "Salesforce CRM"],
        "refresh_cadence": "Weekly Grain"
    },
    "kpi_gross_margin": {
        "id": "kpi_gross_margin",
        "name": "Gross Margin %",
        "category": "Profitability",
        "unit": "%",
        "format": "{:.1f}%",
        "target": 72.0,
        "description": "Gross profit as a percentage of total revenue after COGS and hosting infrastructure.",
        "primary_dimensions": ["region", "product_line"],
        "source_systems": ["Financial Planning Mart"],
        "refresh_cadence": "Monthly Grain"
    },
    "kpi_customer_churn": {
        "id": "kpi_customer_churn",
        "name": "Customer Churn Rate",
        "category": "Customer Retention",
        "unit": "%",
        "format": "{:.2f}%",
        "target": 2.10,
        "description": "Annualized percentage of active recurring contract value lost due to cancellations.",
        "primary_dimensions": ["region", "customer_tier"],
        "source_systems": ["Customer Success Hub"],
        "refresh_cadence": "Weekly Grain"
    },
    "kpi_marketing_roas": {
        "id": "kpi_marketing_roas",
        "name": "Marketing ROAS",
        "category": "Acquisition & Marketing",
        "unit": "x",
        "format": "{:.2f}x",
        "target": 4.20,
        "description": "Return on ad spend across digital acquisition, search, and regional field events.",
        "primary_dimensions": ["channel", "region"],
        "source_systems": ["AdOps Engine"],
        "refresh_cadence": "Daily Grain"
    }
}

# Metric Dependency Graph Metadata
METRIC_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "gross_revenue": {
        "id": "gross_revenue",
        "name": "Gross Revenue",
        "category": "Revenue & Commercial",
        "unit": "$",
        "role": "TARGET",
        "upstream_drivers": ["units_sold", "unit_price", "pricing_complaints", "competitor_activity"],
        "downstream_effects": ["gross_margin", "net_profit"],
        "decomposition_formula": "units_sold * unit_price",
        "expected_direction": {
            "units_sold": "+", # Units sold down -> Revenue down
            "unit_price": "-", # Price up -> Demand volume down (elasticity)
            "pricing_complaints": "-", # Complaints up -> Deal closure down
            "competitor_activity": "-" # Competitor discount up -> Win rate down
        }
    },
    "units_sold": {
        "id": "units_sold",
        "name": "Contract Volume (Units Sold)",
        "category": "Commercial Volume",
        "unit": "Units",
        "role": "UPSTREAM_DIRECT",
        "parent_metric": "gross_revenue",
        "upstream_drivers": ["unit_price", "pricing_complaints", "competitor_activity", "inventory_fill_rate"],
        "downstream_effects": ["gross_revenue", "gross_margin"],
        "expected_direction": {"unit_price": "-", "pricing_complaints": "-"}
    },
    "unit_price": {
        "id": "unit_price",
        "name": "Effective List Unit Price",
        "category": "Commercial Strategy",
        "unit": "$",
        "role": "UPSTREAM_DIRECT",
        "parent_metric": "gross_revenue",
        "upstream_drivers": [],
        "downstream_effects": ["units_sold", "pricing_complaints", "gross_revenue"]
    },
    "pricing_complaints": {
        "id": "pricing_complaints",
        "name": "Customer Pricing Friction (CRM Complaints)",
        "category": "Customer Sentiment",
        "unit": "Tickets/wk",
        "role": "UPSTREAM_INDIRECT",
        "parent_metric": "units_sold",
        "upstream_drivers": ["unit_price"],
        "downstream_effects": ["units_sold", "gross_revenue"]
    },
    "competitor_activity": {
        "id": "competitor_activity",
        "name": "Competitor Rebate & Discount Campaign",
        "category": "External Market",
        "unit": "Discount Index",
        "role": "EXTERNAL_FACTOR",
        "parent_metric": "units_sold",
        "upstream_drivers": [],
        "downstream_effects": ["units_sold", "gross_revenue"]
    },
    "inventory_fill_rate": {
        "id": "inventory_fill_rate",
        "name": "Warehouse Inventory Fill Rate",
        "category": "Supply Chain & Fulfillment",
        "unit": "%",
        "role": "UPSTREAM_INDIRECT",
        "parent_metric": "units_sold",
        "upstream_drivers": [],
        "downstream_effects": ["units_sold"]
    },
    "service_defect_complaints": {
        "id": "service_defect_complaints",
        "name": "Engineering SLA Defect Tickets",
        "category": "Product / Engineering",
        "unit": "Tickets/wk",
        "role": "UPSTREAM_INDIRECT",
        "parent_metric": "units_sold",
        "upstream_drivers": [],
        "downstream_effects": ["units_sold"]
    },
    "gross_margin": {
        "id": "gross_margin",
        "name": "Gross Margin",
        "category": "Profitability",
        "unit": "$ / %",
        "role": "DOWNSTREAM_EFFECT",
        "parent_metric": "gross_revenue",
        "upstream_drivers": ["gross_revenue", "cogs"],
        "downstream_effects": ["net_income"],
        "decomposition_formula": "(gross_revenue - cogs) / gross_revenue"
    },
    "customer_churn": {
        "id": "customer_churn",
        "name": "Customer Churn Rate",
        "category": "Customer Retention",
        "unit": "%",
        "role": "DOWNSTREAM_EFFECT",
        "parent_metric": "gross_revenue",
        "upstream_drivers": [],
        "downstream_effects": ["gross_revenue"]
    }
}

# Structured Candidate Hypotheses Catalog
CANDIDATE_DRIVERS = [
    {
        "id": "H1_PRICING_PRESSURE",
        "name": "Pricing Elasticity & Plan Hike",
        "category": "Commercial Strategy",
        "description": "Targeted +12% price increase on Enterprise tier triggered purchasing pushback, elongated sales cycles, and deal contraction.",
        "expected_lead_time_weeks": [1, 3],
        "controllable": True,
        "lever_type": "price_adjustment",
        "telemetry_available": True,
        "metric_node": "unit_price",
        "dependency_role": "UPSTREAM_DIRECT",
        "required_tables": ["sales", "pricing", "feedback"]
    },
    {
        "id": "H2_COMPETITOR_CAMPAIGN",
        "name": "Aggressive Competitor Campaign",
        "category": "External Market",
        "description": "Direct competitor (ApexTech) launched a localized 15% switcher rebate campaign capturing deal share.",
        "expected_lead_time_weeks": [1, 4],
        "controllable": False,
        "lever_type": "promotional_matching",
        "telemetry_available": True,
        "metric_node": "competitor_activity",
        "dependency_role": "EXTERNAL_FACTOR",
        "required_tables": ["sales", "competitor"]
    },
    {
        "id": "H3_DEMAND_CONTRACTION",
        "name": "Macro Organic Demand Contraction",
        "category": "Macro Environment",
        "description": "Broad macroeconomic software budget contraction compressed category inbound pipeline across regions.",
        "expected_lead_time_weeks": [2, 6],
        "controllable": False,
        "lever_type": "market_diversification",
        "telemetry_available": True,
        "metric_node": "gross_revenue",
        "dependency_role": "EXTERNAL_FACTOR",
        "required_tables": ["sales"]
    },
    {
        "id": "H4_CUSTOMER_CHURN",
        "name": "Customer Retention & Logo Churn",
        "category": "Customer Retention",
        "description": "Elevated customer contract cancellations or early terminations depleted active recurring base.",
        "expected_lead_time_weeks": [0, 2],
        "controllable": True,
        "lever_type": "customer_success_intervention",
        "telemetry_available": True,
        "metric_node": "customer_churn",
        "dependency_role": "DOWNSTREAM_EFFECT",
        "required_tables": ["sales", "feedback"]
    },
    {
        "id": "H5_PRODUCT_DEFECT",
        "name": "Product Quality & SLA Defect",
        "category": "Product / Engineering",
        "description": "Critical software service outages or SLA defects triggered customer payment withholding.",
        "expected_lead_time_weeks": [0, 2],
        "controllable": True,
        "lever_type": "engineering_hotfix",
        "telemetry_available": True,
        "metric_node": "service_defect_complaints",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["feedback"]
    },
    {
        "id": "H6_CHANNEL_EXECUTION",
        "name": "Sales Channel / Partner Friction",
        "category": "Sales Operations",
        "description": "Partner network commission tier restructuring disincentivized regional reseller distribution.",
        "expected_lead_time_weeks": [1, 4],
        "controllable": True,
        "lever_type": "channel_incentive_restructure",
        "telemetry_available": False,
        "metric_node": "channel_friction",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["partner_commissions"]
    },
    {
        "id": "H7_REGIONAL_SHOCK",
        "name": "Regional Geographic Shock",
        "category": "Regional Market",
        "description": "Region-specific regulatory or macroeconomic disruption impacted all commercial commerce in Region B.",
        "expected_lead_time_weeks": [1, 4],
        "controllable": False,
        "lever_type": "regional_allocation",
        "telemetry_available": True,
        "metric_node": "gross_revenue",
        "dependency_role": "EXTERNAL_FACTOR",
        "required_tables": ["sales"]
    },
    {
        "id": "H8_SUPPLY_CONSTRAINT",
        "name": "Supply & Fulfillment Bottleneck",
        "category": "Supply Chain / Fulfillment",
        "description": "Deployment hardware appliance shortages or warehouse logistics backorders constrained delivery.",
        "expected_lead_time_weeks": [0, 2],
        "controllable": True,
        "lever_type": "expedited_fulfillment",
        "telemetry_available": True,
        "metric_node": "inventory_fill_rate",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["inventory"]
    }
]
