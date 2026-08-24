"""
data/generator.py
Synthetic Enterprise Data Generator for EDITH.
Generates coherent, multi-table 52-week relational data containing an embedded causal business scenario.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

def generate_enterprise_dataset(seed: int = 42) -> Dict[str, pd.DataFrame]:
    """
    Generates 52 weeks of interconnected enterprise data across 5 relational tables.
    The data contains a coherent causal scenario centered around Week 06-08 of 2026.
    Calibrated so that global baseline is ~$1.22M/week and drops to ~$1.05M (-14.2%, Z ~ -2.6).
    """
    np.random.seed(seed)
    
    # 52 weeks ending on 2026-02-22 (Week 8 of 2026)
    end_date = datetime(2026, 2, 22)
    weeks = [end_date - timedelta(weeks=51 - i) for i in range(52)]
    week_labels = [f"2025-W{w.isocalendar()[1]:02d}" if w.year == 2025 else f"2026-W{w.isocalendar()[1]:02d}" for w in weeks]
    
    regions = ["Region A", "Region B", "Region C", "Region D"]
    customer_tiers = ["Enterprise", "Mid-Market", "SMB"]
    products = ["Product Suite Alpha", "Product Suite Beta", "Product Suite Gamma"]
    channels = ["Direct Sales", "Partner Network", "Digital"]
    
    # Baseline price catalog ($)
    base_prices = {
        "Product Suite Alpha": {"Enterprise": 10000.0, "Mid-Market": 5000.0, "SMB": 2000.0},
        "Product Suite Beta": {"Enterprise": 4000.0, "Mid-Market": 2000.0, "SMB": 800.0},
        "Product Suite Gamma": {"Enterprise": 2000.0, "Mid-Market": 1000.0, "SMB": 400.0}
    }
    
    # Base units sold per week per segment (calibrated for $1.22M total weekly baseline)
    base_volume_map = {
        ("Region A", "Enterprise", "Product Suite Alpha"): 22,
        ("Region A", "Mid-Market", "Product Suite Alpha"): 16,
        ("Region A", "SMB", "Product Suite Alpha"): 12,
        ("Region B", "Enterprise", "Product Suite Alpha"): 38, # The anomaly focus segment (accounts for ~380k)
        ("Region B", "Mid-Market", "Product Suite Alpha"): 20, # The control cohort
        ("Region B", "SMB", "Product Suite Alpha"): 12,
        ("Region C", "Enterprise", "Product Suite Alpha"): 14,
        ("Region C", "Mid-Market", "Product Suite Alpha"): 10,
        ("Region D", "Enterprise", "Product Suite Alpha"): 10,
        ("Region D", "Mid-Market", "Product Suite Alpha"): 8,
    }
    
    # 1. Fact Table: Sales Weekly
    sales_rows = []
    
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        # Week 49 = 2026-W06 (Price hike introduced on Region B Enterprise Alpha)
        # Week 50 = 2026-W07 (Competitor promotion starts)
        # Week 51 = 2026-W08 (Current week - Material anomaly observed)
        
        is_post_price_hike = (w_idx >= 48) # Week 49+ (W06)
        
        for region in regions:
            for tier in customer_tiers:
                for product in products:
                    for channel in channels:
                        base_vol = base_volume_map.get((region, tier, product), 6)
                        
                        price = base_prices[product][tier]
                        if is_post_price_hike and region == "Region B" and tier == "Enterprise" and product == "Product Suite Alpha":
                            price = 11200.0 # +12% price hike
                        
                        # Standard noise (2.5%)
                        noise = np.random.normal(0, 0.025)
                        volume_mult = 1.0 + noise
                        
                        # Apply acute shock to Region B Enterprise Product Alpha
                        if region == "Region B" and tier == "Enterprise" and product == "Product Suite Alpha":
                            if w_idx == 48: # Week 49 (W06): Initial resistance
                                volume_mult *= 0.88
                            elif w_idx == 49: # Week 50 (W07): Competitor promo active
                                volume_mult *= 0.62
                            elif w_idx >= 50: # Week 51-52 (W08): Full shock
                                volume_mult *= 0.48 # Acute contraction -> ~18 units * 11.2k = ~200k (vs ~380k baseline)
                        elif region == "Region B" and tier == "Mid-Market" and product == "Product Suite Alpha":
                            # Control cohort: un-hiked, remains stable
                            volume_mult *= 0.99
                        
                        channel_shares = {"Direct Sales": 0.55, "Partner Network": 0.30, "Digital": 0.15}
                        units = max(1, int(round(base_vol * channel_shares[channel] * volume_mult)))
                        revenue = units * price
                        cogs = revenue * 0.28 # 28% COGS
                        
                        sales_rows.append({
                            "week_date": w_date.strftime("%Y-%m-%d"),
                            "week_label": w_label,
                            "week_idx": w_idx + 1,
                            "region": region,
                            "customer_tier": tier,
                            "product_line": product,
                            "channel": channel,
                            "units_sold": units,
                            "unit_price": price,
                            "gross_revenue": revenue,
                            "cogs": cogs,
                            "gross_margin": revenue - cogs
                        })
                        
    df_sales = pd.DataFrame(sales_rows)
    
    # 2. Table: Pricing Logs
    pricing_rows = [
        {"log_id": "PRC-2025-01", "effective_date": "2025-01-05", "region": "Global", "customer_tier": "All", "product_line": "All", "price_delta_pct": 0.0, "reason": "Annual baseline reset"},
        {"log_id": "PRC-2026-06", "effective_date": "2026-02-08", "region": "Region B", "customer_tier": "Enterprise", "product_line": "Product Suite Alpha", "price_delta_pct": 12.0, "reason": "Targeted margin optimization policy (W06)"}
    ]
    df_pricing = pd.DataFrame(pricing_rows)
    
    # 3. Table: Competitor Signals
    competitor_rows = []
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        if w_idx >= 49: # Week 50+
            price_index = 0.85 # 15% cheaper
            promo = "Aggressive 15% Switcher Rebate Campaign"
            mentions = np.random.randint(18, 28)
        else:
            price_index = 0.98
            promo = "Standard Tier Pricing"
            mentions = np.random.randint(2, 6)
            
        competitor_rows.append({
            "week_date": w_date.strftime("%Y-%m-%d"),
            "week_label": w_label,
            "week_idx": w_idx + 1,
            "region": "Region B",
            "competitor_name": "ApexTech Solutions",
            "price_index_vs_us": price_index,
            "promo_campaign": promo,
            "crm_win_loss_mentions": mentions
        })
    df_competitor = pd.DataFrame(competitor_rows)
    
    # 4. Table: Inventory & Fulfillment
    inventory_rows = []
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        fill_rate = float(np.clip(np.random.normal(99.4, 0.3), 98.5, 100.0))
        inventory_rows.append({
            "week_date": w_date.strftime("%Y-%m-%d"),
            "week_label": w_label,
            "week_idx": w_idx + 1,
            "region": "Region B",
            "product_line": "Product Suite Alpha",
            "fill_rate_pct": round(fill_rate, 2),
            "stockout_days": 0,
            "status": "Fully Stocked"
        })
    df_inventory = pd.DataFrame(inventory_rows)
    
    # 5. Table: Customer Feedback Signals
    feedback_rows = []
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        if w_idx >= 48: # Post price hike
            price_complaints = np.random.randint(32, 45) # Spike in pricing complaints
            service_complaints = np.random.randint(2, 5)
        else:
            price_complaints = np.random.randint(3, 7)
            service_complaints = np.random.randint(2, 6)
            
        feedback_rows.append({
            "week_date": w_date.strftime("%Y-%m-%d"),
            "week_label": w_label,
            "week_idx": w_idx + 1,
            "region": "Region B",
            "customer_tier": "Enterprise",
            "pricing_complaints_count": price_complaints,
            "service_defect_complaints": service_complaints
        })
    df_feedback = pd.DataFrame(feedback_rows)
    
    return {
        "sales": df_sales,
        "pricing": df_pricing,
        "competitor": df_competitor,
        "inventory": df_inventory,
        "feedback": df_feedback
    }
