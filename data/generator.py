"""
data/generator.py
Synthetic Enterprise Data Generators for EDITH.
Generates multi-table, multi-cadence relational data with unstructured text for 3 calibrated enterprise benchmarks:
1. B2B SaaS Commercial Ledger (Pricing Incident & Competitor Shock)
2. Subscription Growth & Retention (Customer Churn, Marketing ROAS & Sparse History)
3. Regional Retail Demand & Fulfillment (Ambiguous Supplier Stockout vs Weather Event)
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

def generate_enterprise_dataset(seed: int = 42) -> Dict[str, pd.DataFrame]:
    """
    Benchmark 1: B2B SaaS Commercial Ledger (52 weeks, weekly grain).
    Scenario: +12% price hike in Week 06 on Region B Enterprise Alpha -> -14.2% global sales dip.
    """
    np.random.seed(seed)
    
    end_date = datetime(2026, 2, 22)
    weeks = [end_date - timedelta(weeks=51 - i) for i in range(52)]
    week_labels = [f"2025-W{w.isocalendar()[1]:02d}" if w.year == 2025 else f"2026-W{w.isocalendar()[1]:02d}" for w in weeks]
    
    regions = ["Region A", "Region B", "Region C", "Region D"]
    customer_tiers = ["Enterprise", "Mid-Market", "SMB"]
    products = ["Product Suite Alpha", "Product Suite Beta", "Product Suite Gamma"]
    channels = ["Direct Sales", "Partner Network", "Digital"]
    
    base_prices = {
        "Product Suite Alpha": {"Enterprise": 10000.0, "Mid-Market": 5000.0, "SMB": 2000.0},
        "Product Suite Beta": {"Enterprise": 4000.0, "Mid-Market": 2000.0, "SMB": 800.0},
        "Product Suite Gamma": {"Enterprise": 2000.0, "Mid-Market": 1000.0, "SMB": 400.0}
    }
    
    base_volume_map = {
        ("Region A", "Enterprise", "Product Suite Alpha"): 22,
        ("Region A", "Mid-Market", "Product Suite Alpha"): 16,
        ("Region A", "SMB", "Product Suite Alpha"): 12,
        ("Region B", "Enterprise", "Product Suite Alpha"): 38,
        ("Region B", "Mid-Market", "Product Suite Alpha"): 20,
        ("Region B", "SMB", "Product Suite Alpha"): 12,
        ("Region C", "Enterprise", "Product Suite Alpha"): 14,
        ("Region C", "Mid-Market", "Product Suite Alpha"): 10,
        ("Region D", "Enterprise", "Product Suite Alpha"): 10,
        ("Region D", "Mid-Market", "Product Suite Alpha"): 8,
    }
    
    sales_rows = []
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        is_post_price_hike = (w_idx >= 48) # Week 49+ (W06)
        
        for region in regions:
            for tier in customer_tiers:
                for product in products:
                    for channel in channels:
                        base_vol = base_volume_map.get((region, tier, product), 6)
                        price = base_prices[product][tier]
                        if is_post_price_hike and region == "Region B" and tier == "Enterprise" and product == "Product Suite Alpha":
                            price = 11200.0 # +12% price hike
                        
                        noise = np.random.normal(0, 0.025)
                        volume_mult = 1.0 + noise
                        
                        if region == "Region B" and tier == "Enterprise" and product == "Product Suite Alpha":
                            if w_idx == 48:
                                volume_mult *= 0.88
                            elif w_idx == 49:
                                volume_mult *= 0.62
                            elif w_idx >= 50:
                                volume_mult *= 0.48
                        elif region == "Region B" and tier == "Mid-Market" and product == "Product Suite Alpha":
                            volume_mult *= 0.99
                        
                        channel_shares = {"Direct Sales": 0.55, "Partner Network": 0.30, "Digital": 0.15}
                        units = max(1, int(round(base_vol * channel_shares[channel] * volume_mult)))
                        revenue = units * price
                        cogs = revenue * 0.28
                        
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
    
    pricing_rows = [
        {"log_id": "PRC-2025-01", "effective_date": "2025-01-05", "region": "Global", "customer_tier": "All", "product_line": "All", "price_delta_pct": 0.0, "reason": "Annual baseline reset"},
        {"log_id": "PRC-2026-06", "effective_date": "2026-02-08", "region": "Region B", "customer_tier": "Enterprise", "product_line": "Product Suite Alpha", "price_delta_pct": 12.0, "reason": "Targeted margin optimization policy (W06)"}
    ]
    df_pricing = pd.DataFrame(pricing_rows)
    
    competitor_rows = []
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        if w_idx >= 49:
            price_index = 0.85
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
    
    feedback_rows = []
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        if w_idx >= 48:
            price_complaints = np.random.randint(32, 45)
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
    
    feedback_notes = [
        {"note_id": "FB-001", "date": "2026-02-10", "region": "Region B", "customer_tier": "Enterprise", "sentiment": "Negative", "note_text": "Procurement committee stated the unexpected 12% price hike on Product Suite Alpha exceeds their Q1 budget ceiling."},
        {"note_id": "FB-002", "date": "2026-02-12", "region": "Region B", "customer_tier": "Enterprise", "sentiment": "Negative", "note_text": "Customer received competitive quote from ApexTech featuring a 15% discount; renewal paused pending commercial renegotiation."},
        {"note_id": "FB-003", "date": "2026-02-15", "region": "Region B", "customer_tier": "Enterprise", "sentiment": "Neutral", "note_text": "Delivery fulfillment logs confirmed 100% on-time deployment with zero platform bugs."},
        {"note_id": "FB-004", "date": "2026-02-18", "region": "Region A", "customer_tier": "Mid-Market", "sentiment": "Positive", "note_text": "Mid-Market renewal completed smoothly with standard contract terms."}
    ]
    df_feedback_notes = pd.DataFrame(feedback_notes)
    
    return {
        "sales": df_sales,
        "pricing": df_pricing,
        "competitor": df_competitor,
        "inventory": df_inventory,
        "feedback": df_feedback,
        "feedback_notes": df_feedback_notes
    }


def generate_subscription_dataset(seed: int = 42) -> Dict[str, pd.DataFrame]:
    """
    Benchmark 2: Subscription Growth & Retention (Multi-cadence sources).
    Primary KPIs: kpi_customer_churn & kpi_marketing_roas.
    """
    np.random.seed(seed)
    end_date = datetime(2026, 2, 22)
    weeks = [end_date - timedelta(weeks=51 - i) for i in range(52)]
    week_labels = [f"2025-W{w.isocalendar()[1]:02d}" if w.year == 2025 else f"2026-W{w.isocalendar()[1]:02d}" for w in weeks]
    
    regions = ["Region A", "Region B", "Region C", "Region D"]
    customer_tiers = ["Enterprise", "Mid-Market", "Self-Serve Starter"]
    product_tiers = ["Self-Serve Starter", "Professional Suite", "Enterprise Custom"]
    
    # 1. Weekly Fact Table: subscriptions_weekly
    sub_rows = []
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        for reg in regions:
            for c_tier in customer_tiers:
                for p_tier in product_tiers:
                    base_active = 450 if c_tier == "Self-Serve Starter" else (180 if c_tier == "Mid-Market" else 65)
                    mrr_per_sub = 40.0 if c_tier == "Self-Serve Starter" else (250.0 if c_tier == "Mid-Market" else 1500.0)
                    
                    new_subs = int(np.random.normal(25 if c_tier == "Self-Serve Starter" else 8, 2))
                    base_cancels = max(1, int(round(base_active * 0.021))) # ~2.1% baseline churn
                    
                    # Causal shock: Region B Self-Serve Starter onboarding revamp in W48
                    if reg == "Region B" and c_tier == "Self-Serve Starter" and p_tier == "Self-Serve Starter":
                        if w_idx >= 50: # Weeks 51-52 (tau=2-3 weeks post launch)
                            base_cancels = int(round(base_active * 0.086)) # Spike to 8.6% churn (~38-42 cancellations)
                            new_subs = int(new_subs * 0.70)
                    elif reg == "Region A" and c_tier == "Self-Serve Starter":
                        base_cancels = max(1, int(round(base_active * 0.020)))
                    
                    active = max(10, base_active + new_subs - base_cancels)
                    mrr = active * mrr_per_sub
                    
                    sub_rows.append({
                        "week_date": w_date.strftime("%Y-%m-%d"),
                        "week_label": w_label,
                        "week_idx": w_idx + 1,
                        "region": reg,
                        "customer_tier": c_tier,
                        "product_tier": p_tier,
                        "product_line": p_tier,
                        "active_subscriptions": active,
                        "new_subscriptions": new_subs,
                        "cancellations": base_cancels,
                        "mrr": mrr,
                        "gross_revenue": mrr, # Standard alias
                        "units_sold": active
                    })
                    
        # Add Sparse History Segment: 'AI Add-on Beta' (only exists for last 4 weeks: w_idx >= 48)
        if w_idx >= 48:
            sub_rows.append({
                "week_date": w_date.strftime("%Y-%m-%d"),
                "week_label": w_label,
                "week_idx": w_idx + 1,
                "region": "Region B",
                "customer_tier": "Enterprise",
                "product_tier": "AI Add-on Beta",
                "product_line": "AI Add-on Beta",
                "active_subscriptions": 14 + (w_idx - 48) * 3,
                "new_subscriptions": 5,
                "cancellations": 1,
                "mrr": 8400.0 + (w_idx - 48) * 1800.0,
                "gross_revenue": 8400.0 + (w_idx - 48) * 1800.0,
                "units_sold": 14
            })
            
    df_subscriptions = pd.DataFrame(sub_rows)
    
    # 2. Daily Fact Table: marketing_spend_daily (364 days)
    mkt_rows = []
    start_day = end_date - timedelta(days=363)
    channels = ["Search", "Social", "Email", "Partner"]
    
    for d_idx in range(364):
        curr_day = start_day + timedelta(days=d_idx)
        w_idx = d_idx // 7
        is_post_realloc = (d_idx >= 336) # Last 4 weeks (W48+)
        
        for reg in regions:
            for ch in channels:
                if ch == "Search":
                    spend = 300.0 if (is_post_realloc and reg == "Region B") else 1150.0
                    cvr = 0.048
                elif ch == "Social":
                    spend = 1350.0 if (is_post_realloc and reg == "Region B") else 380.0
                    cvr = 0.016 if is_post_realloc else 0.022
                elif ch == "Email":
                    spend = 250.0
                    cvr = 0.035
                else:
                    spend = 400.0
                    cvr = 0.028
                    
                impressions = int(spend * np.random.uniform(28, 35))
                clicks = int(impressions * np.random.uniform(0.025, 0.040))
                conversions = max(1, int(round(clicks * cvr)))
                
                mkt_rows.append({
                    "date": curr_day.strftime("%Y-%m-%d"),
                    "week_idx": w_idx + 1,
                    "channel": ch,
                    "region": reg,
                    "spend_usd": round(spend, 2),
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions
                })
    df_marketing = pd.DataFrame(mkt_rows)
    
    # 3. Monthly Fact Table: support_tickets_monthly (12 months)
    support_rows = []
    months = [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02"]
    ticket_cats = ["Onboarding", "Billing", "Technical", "Other"]
    
    for m_idx, m_str in enumerate(months):
        for reg in regions:
            for c_tier in customer_tiers:
                for cat in ticket_cats:
                    base_tickets = 18 if cat == "Technical" else (12 if cat == "Billing" else 10)
                    if m_str == "2026-02" and reg == "Region B" and c_tier == "Self-Serve Starter" and cat == "Onboarding":
                        base_tickets = 148
                    elif m_str == "2026-02" and reg == "Region A" and cat == "Onboarding":
                        base_tickets = 11
                        
                    support_rows.append({
                        "month": m_str,
                        "region": reg,
                        "customer_tier": c_tier,
                        "category": cat,
                        "ticket_count": int(np.random.normal(base_tickets, 2))
                    })
    df_support = pd.DataFrame(support_rows)
    
    # 4. Unstructured Table: cs_call_notes
    cs_notes = [
        {"note_id": "CS-101", "date": "2026-02-10", "customer_tier": "Self-Serve Starter", "region": "Region B", "segment_tag": "Onboarding", "note_text": "Customer flagged that the new self-serve onboarding flow launched March 3 was confusing and abandoned setup twice before cancelling."},
        {"note_id": "CS-102", "date": "2026-02-12", "customer_tier": "Self-Serve Starter", "region": "Region B", "segment_tag": "Onboarding", "note_text": "Account admin reported that automated workspace provisioning failed silently during setup wizard; user decided to terminate trial."},
        {"note_id": "CS-103", "date": "2026-02-15", "customer_tier": "Self-Serve Starter", "region": "Region B", "segment_tag": "Onboarding", "note_text": "Client feedback: Missing step-by-step checklist in the new portal caused 12 team members to stall during activation."},
        {"note_id": "CS-104", "date": "2026-02-16", "customer_tier": "Enterprise", "region": "Region B", "segment_tag": "Contract", "note_text": "Enterprise account reviewed annual usage; highly satisfied with dedicated CSM support."},
        {"note_id": "CS-105", "date": "2026-02-18", "customer_tier": "Self-Serve Starter", "region": "Region A", "segment_tag": "General", "note_text": "Control cohort customer activated standard starter workspace in under 4 minutes with zero support tickets."}
    ]
    df_cs_notes = pd.DataFrame(cs_notes)
    
    # 5. Unstructured Table: exit_survey_comments
    exit_surveys = [
        {"response_id": "EX-201", "date": "2026-02-11", "customer_tier": "Self-Serve Starter", "region": "Region B", "free_text_reason": "The redesigned onboarding workflow made it impossible for our team to get started without filing support tickets. Cancelling."},
        {"response_id": "EX-202", "date": "2026-02-14", "customer_tier": "Self-Serve Starter", "region": "Region B", "free_text_reason": "Setup wizard looped indefinitely on user invite step; customer success was too slow to respond."},
        {"response_id": "EX-203", "date": "2026-02-17", "customer_tier": "Self-Serve Starter", "region": "Region B", "free_text_reason": "Pricing is fair, but our trial expired before we could finish the confusing multi-step workspace calibration."}
    ]
    df_exit_surveys = pd.DataFrame(exit_surveys)
    
    return {
        "subscriptions_weekly": df_subscriptions,
        "sales": df_subscriptions,
        "marketing_spend_daily": df_marketing,
        "support_tickets_monthly": df_support,
        "cs_call_notes": df_cs_notes,
        "exit_survey_comments": df_exit_surveys
    }


def generate_retail_dataset(seed: int = 42) -> Dict[str, pd.DataFrame]:
    """
    Benchmark 3: Regional Retail Demand & Fulfillment (Different industry & deliberately ambiguous).
    Primary KPIs: kpi_retail_sales & kpi_stockout_rate.
    """
    np.random.seed(seed)
    end_date = datetime(2026, 2, 22)
    weeks = [end_date - timedelta(weeks=51 - i) for i in range(52)]
    week_labels = [f"2025-W{w.isocalendar()[1]:02d}" if w.year == 2025 else f"2026-W{w.isocalendar()[1]:02d}" for w in weeks]
    
    regions = ["Region North", "Region South", "Region East", "Region West"]
    store_categories = ["Apparel & Home", "Electronics", "Groceries", "Health & Beauty"]
    
    # 1. Weekly Fact Table: store_sales_weekly
    sales_rows = []
    for w_idx, (w_date, w_label) in enumerate(zip(weeks, week_labels)):
        for reg in regions:
            for cat in store_categories:
                base_sales = 210000.0 if cat == "Apparel & Home" else (160000.0 if cat == "Electronics" else 125000.0)
                base_units = int(base_sales / 45.0)
                base_traffic = 14500
                
                noise = np.random.normal(1.0, 0.02)
                sales_val = base_sales * noise
                units_val = int(base_units * noise)
                traffic_val = int(base_traffic * noise)
                
                if reg == "Region North" and cat == "Apparel & Home":
                    if w_idx >= 50:
                        sales_val = base_sales * 0.562
                        units_val = int(base_units * 0.562)
                        traffic_val = int(base_traffic * 0.66)
                elif reg == "Region South" and cat == "Apparel & Home":
                    sales_val = base_sales * 0.99
                
                sales_rows.append({
                    "week_date": w_date.strftime("%Y-%m-%d"),
                    "week_label": w_label,
                    "week_idx": w_idx + 1,
                    "region": reg,
                    "store_category": cat,
                    "sales_usd": round(sales_val, 2),
                    "gross_revenue": round(sales_val, 2),
                    "units_sold": units_val,
                    "unit_price": 45.0,
                    "foot_traffic": traffic_val,
                    "customer_tier": "Retail Store",
                    "product_line": cat
                })
    df_store_sales = pd.DataFrame(sales_rows)
    
    # 2. Daily Fact Table: inventory_daily (364 days)
    inv_rows = []
    start_day = end_date - timedelta(days=363)
    for d_idx in range(364):
        curr_day = start_day + timedelta(days=d_idx)
        w_idx = d_idx // 7
        is_shock_window = (d_idx >= 343)
        
        for reg in regions:
            for cat in store_categories:
                base_stock = 4500
                stockout = 0
                if reg == "Region North" and cat == "Apparel & Home" and is_shock_window:
                    base_stock = int(np.random.normal(1200, 150))
                    stockout = 1 if np.random.rand() < 0.48 else 0
                
                inv_rows.append({
                    "date": curr_day.strftime("%Y-%m-%d"),
                    "week_idx": w_idx + 1,
                    "region": reg,
                    "sku_category": cat,
                    "stock_on_hand": max(0, base_stock),
                    "stockout_flag": stockout
                })
    df_inventory_daily = pd.DataFrame(inv_rows)
    
    # 3. Irregular Event Table: supplier_shipment_logs
    shipment_rows = [
        {"shipment_id": "SHP-8801", "scheduled_date": "2026-01-28", "actual_date": "2026-02-09", "region": "Region North", "sku_category": "Apparel & Home", "delay_days": 12, "status": "Customs Hold / Port Clearance Delay"},
        {"shipment_id": "SHP-8802", "scheduled_date": "2026-02-03", "actual_date": "2026-02-14", "region": "Region North", "sku_category": "Apparel & Home", "delay_days": 11, "status": "Container Terminal Congestion"},
        {"shipment_id": "SHP-8803", "scheduled_date": "2026-02-05", "actual_date": "2026-02-06", "region": "Region South", "sku_category": "Apparel & Home", "delay_days": 1, "status": "On-Time Fulfillment"},
        {"shipment_id": "SHP-8804", "scheduled_date": "2026-02-10", "actual_date": "2026-02-19", "region": "Region North", "sku_category": "Electronics", "delay_days": 9, "status": "Carrier Transit Delay"}
    ]
    df_shipment_logs = pd.DataFrame(shipment_rows)
    
    # 4. Monthly Fact Table: regional_events_monthly (12 months)
    event_rows = []
    months = [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02"]
    for m_idx, m_str in enumerate(months):
        for reg in regions:
            weather_idx = float(np.random.uniform(1.2, 3.5))
            local_event = False
            if m_str == "2026-02" and reg == "Region North":
                weather_idx = 8.7
                local_event = True
            event_rows.append({
                "month": m_str,
                "region": reg,
                "weather_severity_index": round(weather_idx, 1),
                "local_event_flag": local_event
            })
    df_regional_events = pd.DataFrame(event_rows)
    
    # 5. Unstructured Table: supplier_emails
    supplier_emails = [
        {"email_id": "EML-401", "date": "2026-02-04", "region": "Region North", "sku_category": "Apparel & Home", "email_text": "Customs hold at Seattle container port extended cargo inspection by 12 days; Spring apparel pallets cannot be dispatched until clearance."},
        {"email_id": "EML-402", "date": "2026-02-08", "region": "Region North", "sku_category": "Apparel & Home", "email_text": "Regional distribution hub is currently frozen due to extreme ice storms; freight carrier routes into Region North are operating at 40% capacity."},
        {"email_id": "EML-403", "date": "2026-02-12", "region": "Region North", "sku_category": "Apparel & Home", "email_text": "Supplier update: Alternate inland freight carrier has been contracted, but transit ETA is pushed to next Friday."}
    ]
    df_supplier_emails = pd.DataFrame(supplier_emails)
    
    # 6. Unstructured Table: customer_reviews
    customer_reviews = [
        {"review_id": "REV-501", "date": "2026-02-11", "region": "Region North", "store_category": "Apparel & Home", "rating": 1, "review_text": "Visited the North flagship store twice this week; apparel shelves were completely empty and store associates had no restock timeline."},
        {"review_id": "REV-502", "date": "2026-02-14", "region": "Region North", "store_category": "Apparel & Home", "rating": 2, "review_text": "Drove 30 minutes in the freezing blizzard to buy winter home goods, only to find the entire department cordoned off due to stockouts."},
        {"review_id": "REV-503", "date": "2026-02-16", "region": "Region South", "store_category": "Apparel & Home", "rating": 5, "review_text": "Great shopping experience at the South branch; everything in stock and quick checkout."}
    ]
    df_customer_reviews = pd.DataFrame(customer_reviews)
    
    return {
        "store_sales_weekly": df_store_sales,
        "sales": df_store_sales,
        "inventory_daily": df_inventory_daily,
        "supplier_shipment_logs": df_shipment_logs,
        "regional_events_monthly": df_regional_events,
        "supplier_emails": df_supplier_emails,
        "customer_reviews": df_customer_reviews
    }
