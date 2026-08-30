"""
config/semantic_contracts.py
Governed KPI definitions, metric dependency definitions, dimension metadata, and candidate driver catalogs
for all 3 calibrated enterprise benchmarks:
1. B2B SaaS Sales Pricing Incident (b2b_saas_pricing)
2. Subscription Growth & Retention (saas_churn_roas)
3. Regional Retail Demand & Fulfillment (retail_fulfillment)
"""
from typing import Dict, List, Any

# Governed KPI definitions across all benchmarks
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
        "description": "Annualized percentage of active recurring subscriptions lost due to cancellations.",
        "primary_dimensions": ["region", "customer_tier", "product_tier"],
        "source_systems": ["Subscription Billing Ledger", "Support Ticket Mart", "CS Call Notes"],
        "refresh_cadence": "Multi-Cadence (Weekly / Monthly / Free-text)"
    },
    "kpi_marketing_roas": {
        "id": "kpi_marketing_roas",
        "name": "Marketing ROAS",
        "category": "Acquisition & Marketing",
        "unit": "x",
        "format": "{:.2f}x",
        "target": 4.20,
        "description": "Return on ad spend across Search, Social, Email, and Partner acquisition channels.",
        "primary_dimensions": ["channel", "region"],
        "source_systems": ["AdOps Engine Daily Feeds"],
        "refresh_cadence": "Daily Grain"
    },
    "kpi_retail_sales": {
        "id": "kpi_retail_sales",
        "name": "Weekly Store Revenue",
        "category": "Retail Commercial",
        "unit": "$",
        "format": "${:,.0f}",
        "target": 210_000,
        "description": "Weekly store sales revenue across Apparel, Electronics, Groceries, and Home departments.",
        "primary_dimensions": ["region", "store_category"],
        "source_systems": ["POS Store Ledgers", "Supplier Logistics", "Customer Reviews"],
        "refresh_cadence": "Multi-Cadence (Weekly / Daily / Irregular)"
    },
    "kpi_stockout_rate": {
        "id": "kpi_stockout_rate",
        "name": "Store Stockout Rate",
        "category": "Supply Chain & Fulfillment",
        "unit": "%",
        "format": "{:.1f}%",
        "target": 2.0,
        "description": "Percentage of daily active SKU inventory out of stock on store shelves.",
        "primary_dimensions": ["region", "sku_category"],
        "source_systems": ["WMS Inventory Daily Logs", "Supplier Shipment Manifests"],
        "refresh_cadence": "Daily / Event-based Grain"
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
        "upstream_drivers": ["units_sold", "unit_price", "pricing_complaints", "competitor_activity", "cancellations", "foot_traffic", "stockout_flag"],
        "downstream_effects": ["gross_margin", "net_profit", "mrr"],
        "decomposition_formula": "units_sold * unit_price",
        "expected_direction": {
            "units_sold": "+",
            "unit_price": "-",
            "pricing_complaints": "-",
            "competitor_activity": "-",
            "cancellations": "-",
            "foot_traffic": "+",
            "stockout_flag": "-"
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
        "role": "TARGET",
        "upstream_drivers": ["onboarding_tickets", "cs_call_friction", "exit_surveys"],
        "downstream_effects": ["mrr", "gross_revenue"]
    },
    "marketing_roas": {
        "id": "marketing_roas",
        "name": "Marketing ROAS",
        "category": "Marketing Acquisition",
        "unit": "x",
        "role": "UPSTREAM_INDIRECT",
        "upstream_drivers": ["channel_spend", "conversion_rate"],
        "downstream_effects": ["new_subscriptions"]
    },
    "stockout_flag": {
        "id": "stockout_flag",
        "name": "Store Shelf Stockouts",
        "category": "Supply Chain",
        "unit": "Stockout Rate %",
        "role": "UPSTREAM_DIRECT",
        "upstream_drivers": ["supplier_delays"],
        "downstream_effects": ["store_sales_weekly"]
    },
    "foot_traffic": {
        "id": "foot_traffic",
        "name": "Retail Store Foot Traffic",
        "category": "Customer Demand",
        "unit": "Shoppers/wk",
        "role": "EXTERNAL_FACTOR",
        "upstream_drivers": ["weather_severity"],
        "downstream_effects": ["store_sales_weekly"]
    }
}

# ==============================================================================
# CANDIDATE HYPOTHESIS CATALOGS BY BENCHMARK
# ==============================================================================

# Catalog 1: B2B SaaS Sales Pricing Incident (Original Benchmark)
CANDIDATE_DRIVERS_PRICING = [
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
        "name": "Account Cancellation Wave",
        "category": "Customer Retention",
        "description": "Elevated customer contract churn and mid-cycle subscription cancellations drained recurring revenue baseline.",
        "expected_lead_time_weeks": [1, 3],
        "controllable": True,
        "lever_type": "csm_intervention",
        "telemetry_available": True,
        "metric_node": "customer_churn",
        "dependency_role": "DOWNSTREAM_EFFECT",
        "required_tables": ["sales", "feedback"]
    },
    {
        "id": "H5_PRODUCT_DEFECT",
        "name": "Core Platform Outage / Defect",
        "category": "Product / Engineering",
        "description": "Unresolved Sev-1 software bugs and platform downtime degraded user experience, driving buyer dissatisfaction.",
        "expected_lead_time_weeks": [0, 2],
        "controllable": True,
        "lever_type": "qa_remediation",
        "telemetry_available": True,
        "metric_node": "service_defect_complaints",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["feedback"]
    },
    {
        "id": "H6_CHANNEL_EXECUTION",
        "name": "Partner Channel Commission Friction",
        "category": "Partner Operations",
        "description": "Restructuring of regional reseller commission splits disincentivized tier-1 channel partners.",
        "expected_lead_time_weeks": [2, 4],
        "controllable": True,
        "lever_type": "commission_realignment",
        "telemetry_available": False, # Intentionally missing to demonstrate NOT_TESTABLE
        "metric_node": "channel_commissions",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["partner_commissions"]
    },
    {
        "id": "H7_REGIONAL_SHOCK",
        "name": "Localized Regulatory / Tax Event",
        "category": "Macro Environment",
        "description": "Sudden localized corporate compliance mandates in Region B delayed enterprise procurement sign-offs.",
        "expected_lead_time_weeks": [1, 4],
        "controllable": False,
        "lever_type": "legal_structuring",
        "telemetry_available": True,
        "metric_node": "gross_revenue",
        "dependency_role": "EXTERNAL_FACTOR",
        "required_tables": ["sales"]
    },
    {
        "id": "H8_SUPPLY_CONSTRAINT",
        "name": "Hardware Fulfillment / Inventory Outage",
        "category": "Supply Chain",
        "description": "Severe supply chain stockouts prevented customer onboarding and hardware token delivery.",
        "expected_lead_time_weeks": [0, 2],
        "controllable": True,
        "lever_type": "inventory_reallocation",
        "telemetry_available": True,
        "metric_node": "inventory_fill_rate",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["inventory"]
    }
]

# Catalog 2: Subscription Growth & Retention (saas_churn_roas)
CANDIDATE_DRIVERS_SUBSCRIPTIONS = [
    {
        "id": "S1_ONBOARDING_FLOW_CHANGE",
        "name": "Self-Serve Onboarding Flow Redesign",
        "category": "Product Experience",
        "description": "New self-serve onboarding wizard launched in Week 48 created user confusion and silent setup abandonment, driving a sharp surge in cancellations 2 weeks later.",
        "expected_lead_time_weeks": [2, 3],
        "controllable": True,
        "lever_type": "onboarding_rollback",
        "telemetry_available": True,
        "metric_node": "customer_churn",
        "dependency_role": "UPSTREAM_DIRECT",
        "required_tables": ["subscriptions_weekly", "support_tickets_monthly", "cs_call_notes", "exit_survey_comments"]
    },
    {
        "id": "S2_MARKETING_REALLOCATION",
        "name": "Acquisition Channel Budget Shift",
        "category": "Marketing Operations",
        "description": "Reallocating ad spend from high-intent Search to broad Social in Week 48 degraded inbound lead conversion and depressed Marketing ROAS (Confounder against Churn).",
        "expected_lead_time_weeks": [0, 2],
        "controllable": True,
        "lever_type": "channel_rebalance",
        "telemetry_available": True,
        "metric_node": "marketing_roas",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["marketing_spend_daily"]
    },
    {
        "id": "S3_MRR_CONTRACTION",
        "name": "Monthly Recurring Revenue (MRR) Contraction",
        "category": "Financial Impact",
        "description": "Loss of active subscription cohorts directly eroded monthly recurring revenue (MRR) baseline in Region B.",
        "expected_lead_time_weeks": [0, 1],
        "controllable": False,
        "lever_type": "financial_hedging",
        "telemetry_available": True,
        "metric_node": "gross_revenue",
        "dependency_role": "DOWNSTREAM_EFFECT",
        "required_tables": ["subscriptions_weekly"]
    },
    {
        "id": "S4_COMPETITOR_POACHING",
        "name": "Competitor Head-Hunting & Poaching",
        "category": "External Market",
        "description": "Competitor targeted mid-market active logos with free migration credits and custom buyout incentives.",
        "expected_lead_time_weeks": [1, 4],
        "controllable": False,
        "lever_type": "contract_lockin",
        "telemetry_available": False, # Intentionally missing to demonstrate NOT_TESTABLE
        "metric_node": "competitor_poaching_feed",
        "dependency_role": "EXTERNAL_FACTOR",
        "required_tables": ["competitor_intel_feed"]
    }
]

# Catalog 3: Regional Retail Demand & Fulfillment (retail_fulfillment)
CANDIDATE_DRIVERS_RETAIL = [
    {
        "id": "R1_SUPPLIER_STOCKOUT",
        "name": "Port Freight Delays & In-Store Stockouts",
        "category": "Supply Chain & Logistics",
        "description": "Customs clearance bottlenecks at the Seattle container terminal triggered 9-12 day shipment delays and empty apparel shelves (48% stockout rate in Region North).",
        "expected_lead_time_weeks": [1, 2],
        "controllable": True,
        "lever_type": "expedite_supplier",
        "telemetry_available": True,
        "metric_node": "stockout_flag",
        "dependency_role": "UPSTREAM_DIRECT",
        "required_tables": ["inventory_daily", "supplier_shipment_logs", "supplier_emails", "customer_reviews"]
    },
    {
        "id": "R2_REGIONAL_WEATHER_EVENT",
        "name": "Extreme Winter Storm & Foot Traffic Dip",
        "category": "External Environment",
        "description": "Historic blizzard conditions in Region North suppressed retail store foot traffic by -34% during the exact same February window (Competing Ambiguous Driver).",
        "expected_lead_time_weeks": [0, 1],
        "controllable": False,
        "lever_type": "omnichannel_fulfillment",
        "telemetry_available": True,
        "metric_node": "foot_traffic",
        "dependency_role": "EXTERNAL_FACTOR",
        "required_tables": ["regional_events_monthly", "store_sales_weekly"]
    },
    {
        "id": "R3_PRICING_CHANGE",
        "name": "Store List Price Adjustments",
        "category": "Commercial Strategy",
        "description": "Retail price adjustments on core apparel and home goods categories dampened customer purchasing volume.",
        "expected_lead_time_weeks": [1, 3],
        "controllable": True,
        "lever_type": "price_adjustment",
        "telemetry_available": True,
        "metric_node": "unit_price",
        "dependency_role": "UPSTREAM_DIRECT",
        "required_tables": ["store_sales_weekly"]
    },
    {
        "id": "R4_COMPETITOR_STORE_OPENING",
        "name": "Competitor Superstore Grand Opening",
        "category": "External Market",
        "description": "Adjacent discount supercenter opened 2 miles from flagship store, cannibalizing local shopper footfall.",
        "expected_lead_time_weeks": [2, 6],
        "controllable": False,
        "lever_type": "loyalty_incentives",
        "telemetry_available": False, # Intentionally missing to demonstrate NOT_TESTABLE
        "metric_node": "competitor_permits",
        "dependency_role": "EXTERNAL_FACTOR",
        "required_tables": ["competitor_permits"]
    }
]

# Backwards compatibility default alias
CANDIDATE_DRIVERS = CANDIDATE_DRIVERS_PRICING

CANDIDATE_DRIVERS_MANUFACTURING = [
    {
        "id": "M1_CALIBRATION_DRIFT",
        "name": "Machine Calibration Drift (M-07 Weld Station)",
        "category": "Equipment & Maintenance",
        "description": "Worn servo motor encoder on M-07 weld station (Line 3, Plant Midwest) causing progressive calibration drift from 0.2% to 4.8%, degrading first-pass yield on housing seam welds.",
        "expected_lead_time_weeks": [1, 3],
        "controllable": True,
        "lever_type": "emergency_recalibration",
        "telemetry_available": True,
        "metric_node": "first_pass_yield",
        "dependency_role": "UPSTREAM_DIRECT",
        "required_tables": ["production_output_daily", "machine_calibration_logs", "qc_inspector_notes", "maintenance_tickets"]
    },
    {
        "id": "M2_SUPPLIER_MATERIAL_QUALITY",
        "name": "Incoming Material Quality Degradation (SUP-03)",
        "category": "Supply Chain & Materials",
        "description": "Supplier SUP-03 material quality scores dipped from 94 to 82 on an overlapping but not identical window, creating a confounding secondary signal.",
        "expected_lead_time_weeks": [2, 4],
        "controllable": True,
        "lever_type": "reject_supplier_batch",
        "telemetry_available": True,
        "metric_node": "material_quality",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["supplier_material_certs_weekly"]
    },
    {
        "id": "M3_OPERATOR_SHIFT_CHANGE",
        "name": "Shift Pattern & Operator Tenure Change",
        "category": "Workforce & Operations",
        "description": "Changes in shift schedule or operator experience levels potentially degrading quality through human factors.",
        "expected_lead_time_weeks": [1, 4],
        "controllable": True,
        "lever_type": "operator_training",
        "telemetry_available": True,
        "metric_node": "operator_performance",
        "dependency_role": "UPSTREAM_INDIRECT",
        "required_tables": ["shift_roster_monthly"]
    },
    {
        "id": "M4_HUMIDITY_TRANSIT_EXPOSURE",
        "name": "Raw Material Humidity Exposure During Transit",
        "category": "Logistics & Environment",
        "description": "Potential moisture exposure during raw material transportation causing material property degradation. No transit environment monitoring telemetry exists.",
        "expected_lead_time_weeks": [2, 6],
        "controllable": False,
        "lever_type": "none",
        "telemetry_available": False,
        "metric_node": "transit_environment",
        "dependency_role": "EXTERNAL_FACTOR",
        "required_tables": ["transit_humidity_logs"]
    }
]

def get_candidate_drivers(benchmark_id: str = "b2b_saas_pricing") -> List[Dict[str, Any]]:
    """Returns candidate drivers tailored to the active calibrated benchmark."""
    if benchmark_id == "saas_churn_roas":
        return CANDIDATE_DRIVERS_SUBSCRIPTIONS
    elif benchmark_id == "retail_fulfillment":
        return CANDIDATE_DRIVERS_RETAIL
    elif benchmark_id == "manufacturing_quality":
        return CANDIDATE_DRIVERS_MANUFACTURING
    return CANDIDATE_DRIVERS_PRICING
