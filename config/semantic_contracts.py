"""
config/semantic_contracts.py
Governed KPI definitions, hierarchies, dimension metadata, and candidate driver catalog.
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

# Candidate Hypotheses / Drivers Catalog for Revenue Anomalies
CANDIDATE_DRIVERS = [
    {
        "id": "H1_PRICING_PRESSURE",
        "name": "Pricing Elasticity & Plan Hike",
        "category": "Commercial Strategy",
        "description": "Price increase on Enterprise tier triggered purchasing pushback and elongated sales cycles.",
        "expected_lead_time_weeks": [1, 3],
        "controllable": True,
        "lever_type": "price_adjustment"
    },
    {
        "id": "H2_COMPETITOR_CAMPAIGN",
        "name": "Aggressive Competitor Campaign",
        "category": "External Market",
        "description": "Direct competitor launched a localized price-cut/rebate campaign capturing deal share.",
        "expected_lead_time_weeks": [1, 4],
        "controllable": False,
        "lever_type": "promotional_matching"
    },
    {
        "id": "H3_INVENTORY_CONSTRAINT",
        "name": "Inventory & Fulfillment Bottleneck",
        "category": "Supply Chain / Fulfillment",
        "description": "Deployment delays or hardware appliance stockouts constrained delivery.",
        "expected_lead_time_weeks": [0, 2],
        "controllable": True,
        "lever_type": "expedited_fulfillment"
    },
    {
        "id": "H4_DEMAND_CONTRACTION",
        "name": "Macro Organic Demand Contraction",
        "category": "Macro Environment",
        "description": "Broad macroeconomic slowdown reduced total category pipeline and customer inbound volume.",
        "expected_lead_time_weeks": [2, 6],
        "controllable": False,
        "lever_type": "market_diversification"
    }
]
