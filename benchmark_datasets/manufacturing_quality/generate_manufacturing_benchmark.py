"""
Manufacturing Quality & Supply Chain Benchmark Generator
=========================================================
Generates 6 CSV files for the 4th calibrated EDITH benchmark.

Causal Story:
- Machine M-07 on Line 3 at Plant Midwest develops calibration drift (weeks 46-49)
- This causes first-pass yield to drop from ~96% to ~78% starting week 48
- Confounding signal: Supplier SUP-03 material quality dips in overlapping window
- REFUTED: Shift patterns / operator tenure are stable (no correlation)
- NOT TESTABLE: Raw material humidity during transit (no telemetry)

Fiscal Calendar: Fiscal week = ISO week + 2 (offset documented here)
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

SEED = 42

def generate_all(output_dir):
    np.random.seed(SEED)
    
    end_date = datetime(2026, 2, 22)
    daily_dates = [end_date - timedelta(days=363 - i) for i in range(364)]
    weekly_dates = [end_date - timedelta(weeks=51 - i) for i in range(52)]
    
    plants = ["Plant Midwest", "Plant Southeast"]
    lines = ["Line 1", "Line 2", "Line 3"]
    models_list = ["Model-A", "Model-B", "Model-C"]
    
    # =========================================================================
    # 1. production_output_daily.csv
    # =========================================================================
    prod_rows = []
    for d in daily_dates:
        iso_week = d.isocalendar()[1]
        iso_year = d.isocalendar()[0]
        for plant in plants:
            for line in lines:
                for model in models_list:
                    base_units = 120 + np.random.randint(-10, 10)
                    base_yield = 96.2 + np.random.normal(0, 0.8)
                    
                    is_shocked = (plant == "Plant Midwest" and line == "Line 3" 
                                  and iso_year == 2026 and iso_week >= 4)
                    if is_shocked:
                        weeks_since = iso_week - 3
                        drift_impact = min(18.0, 3.0 * weeks_since + np.random.normal(0, 1.5))
                        base_yield = max(65.0, 96.2 - drift_impact)
                        base_units = int(base_units * 0.92)
                    
                    base_yield = min(99.5, max(60.0, base_yield))
                    units_passed = int(base_units * base_yield / 100.0)
                    
                    prod_rows.append({
                        "date": d.strftime("%Y-%m-%d"),
                        "iso_week": f"{iso_year}-W{iso_week:02d}",
                        "plant": plant,
                        "line_id": line,
                        "product_model": model,
                        "units_produced": base_units,
                        "units_passed_qc": units_passed,
                        "yield_pct": round(base_yield, 1)
                    })
    
    df_prod = pd.DataFrame(prod_rows)
    df_prod.to_csv(os.path.join(output_dir, "production_output_daily.csv"), index=False)
    print(f"  production_output_daily.csv: {len(df_prod)} rows")
    
    # =========================================================================
    # 2. machine_calibration_logs.csv (irregular/event-based)
    # =========================================================================
    cal_rows = []
    cal_id = 100
    machines = ["M-01", "M-02", "M-03", "M-04", "M-05", "M-06", "M-07", "M-08"]
    technicians = ["T. Rodriguez", "A. Chen", "M. Patel", "K. Johnson"]
    
    for _ in range(30):
        cal_id += 1
        d = daily_dates[np.random.randint(0, len(daily_dates))]
        plant = np.random.choice(plants)
        line = np.random.choice(lines)
        machine = np.random.choice(machines)
        drift = round(abs(np.random.normal(0.3, 0.4)), 2)
        tech = np.random.choice(technicians)
        cal_rows.append({
            "calibration_id": f"CAL-{cal_id}",
            "date": d.strftime("%Y-%m-%d"),
            "plant": plant,
            "line_id": line,
            "machine_id": machine,
            "calibration_drift_pct": drift,
            "technician": tech
        })
    
    shock_dates = [
        datetime(2026, 1, 12), datetime(2026, 1, 19),
        datetime(2026, 1, 26), datetime(2026, 2, 2), datetime(2026, 2, 9),
    ]
    drifts = [1.2, 2.1, 3.4, 4.1, 4.8]
    for d, drift in zip(shock_dates, drifts):
        cal_id += 1
        cal_rows.append({
            "calibration_id": f"CAL-{cal_id}",
            "date": d.strftime("%Y-%m-%d"),
            "plant": "Plant Midwest",
            "line_id": "Line 3",
            "machine_id": "M-07",
            "calibration_drift_pct": drift,
            "technician": "T. Rodriguez"
        })
    
    df_cal = pd.DataFrame(cal_rows).sort_values("date").reset_index(drop=True)
    df_cal.to_csv(os.path.join(output_dir, "machine_calibration_logs.csv"), index=False)
    print(f"  machine_calibration_logs.csv: {len(df_cal)} rows")
    
    # =========================================================================
    # 3. supplier_material_certs_weekly.csv (FISCAL calendar, offset +2 from ISO)
    # =========================================================================
    suppliers = ["SUP-01", "SUP-02", "SUP-03", "SUP-04"]
    mat_rows = []
    batch_id = 1000
    
    for w_idx in range(52):
        fiscal_week = ((w_idx + 2) % 52) + 1
        fiscal_label = f"FY26-FW{fiscal_week:02d}"
        
        for plant in plants:
            for sup in suppliers:
                batch_id += 1
                base_quality = 94.0 + np.random.normal(0, 1.5)
                
                if sup == "SUP-03" and fiscal_week >= 50:
                    base_quality = 82.0 + np.random.normal(0, 2.0)
                elif sup == "SUP-03" and fiscal_week >= 47:
                    base_quality = 88.0 + np.random.normal(0, 1.5)
                
                base_quality = min(99.0, max(70.0, base_quality))
                
                mat_rows.append({
                    "fiscal_week": fiscal_label,
                    "supplier_id": sup,
                    "material_batch_id": f"BATCH-{batch_id}",
                    "material_quality_score": round(base_quality, 1),
                    "plant": plant
                })
    
    df_mat = pd.DataFrame(mat_rows)
    df_mat.to_csv(os.path.join(output_dir, "supplier_material_certs_weekly.csv"), index=False)
    print(f"  supplier_material_certs_weekly.csv: {len(df_mat)} rows")
    
    # =========================================================================
    # 4. shift_roster_monthly.csv (REFUTED hypothesis data)
    # =========================================================================
    months = [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02"]
    roster_rows = []
    
    for month in months:
        for plant in plants:
            for line in lines:
                shift = np.random.choice(["Day", "Swing", "Night"])
                tenure = round(24.0 + np.random.normal(0, 3.0), 1)
                tenure = max(6.0, tenure)
                roster_rows.append({
                    "month": month,
                    "plant": plant,
                    "line_id": line,
                    "shift_pattern": shift,
                    "avg_operator_tenure_months": tenure
                })
    
    df_roster = pd.DataFrame(roster_rows)
    df_roster.to_csv(os.path.join(output_dir, "shift_roster_monthly.csv"), index=False)
    print(f"  shift_roster_monthly.csv: {len(df_roster)} rows")
    
    # =========================================================================
    # 5. qc_inspector_notes.csv (unstructured free-text)
    # =========================================================================
    qc_notes = [
        {"note_id": "QC-001", "date": "2025-06-15", "plant": "Plant Midwest", "line_id": "Line 1", "inspector": "J. Kim",
         "note_text": "Routine inspection passed. All weld seams within tolerance. No defect clusters observed."},
        {"note_id": "QC-002", "date": "2025-08-22", "plant": "Plant Southeast", "line_id": "Line 2", "inspector": "R. Gomez",
         "note_text": "Minor cosmetic blemish on batch BT-4412 housing, within acceptable limits. Passed QC."},
        {"note_id": "QC-003", "date": "2025-10-10", "plant": "Plant Midwest", "line_id": "Line 3", "inspector": "J. Kim",
         "note_text": "Standard calibration check on M-07 completed. Drift within normal range (0.3%). All units passed."},
        {"note_id": "QC-004", "date": "2025-11-18", "plant": "Plant Midwest", "line_id": "Line 1", "inspector": "S. Okafor",
         "note_text": "Full batch inspection of Model-B run. Zero defects detected. Excellent weld consistency."},
        {"note_id": "QC-005", "date": "2026-01-14", "plant": "Plant Midwest", "line_id": "Line 3", "inspector": "J. Kim",
         "note_text": "Noticed slight misalignment on housing seam welds for Model-A units. M-07 calibration drift may be starting to affect output. Flagged for maintenance review."},
        {"note_id": "QC-006", "date": "2026-01-21", "plant": "Plant Midwest", "line_id": "Line 3", "inspector": "J. Kim",
         "note_text": "Defect clustering on housing seam weld is getting worse this week. Almost 1 in 5 units failing first-pass QC. M-07 drift observed again this shift — technician Rodriguez confirmed drift at 2.1% which is above our 1.0% action threshold."},
        {"note_id": "QC-007", "date": "2026-01-28", "plant": "Plant Midwest", "line_id": "Line 3", "inspector": "S. Okafor",
         "note_text": "Line 3 yield continues to deteriorate. Housing seam weld failures now account for 60% of all rejects. M-07 calibration drift is clearly the root cause — drift reading at 3.4% as of this morning. Recommend emergency recalibration."},
        {"note_id": "QC-008", "date": "2026-02-03", "plant": "Plant Midwest", "line_id": "Line 3", "inspector": "J. Kim",
         "note_text": "Worst week yet for Line 3. First-pass yield dropped below 80%. All failures trace back to M-07 weld station. Drift now at 4.1%. Production manager escalated to plant director."},
        {"note_id": "QC-009", "date": "2026-02-10", "plant": "Plant Midwest", "line_id": "Line 3", "inspector": "J. Kim",
         "note_text": "M-07 drift measured at 4.8%. Emergency recalibration request submitted but waiting on parts. Meanwhile, secondary visual inspection checkpoint added after M-07 station to catch defects before final assembly."},
        {"note_id": "QC-010", "date": "2026-01-15", "plant": "Plant Midwest", "line_id": "Line 2", "inspector": "R. Gomez",
         "note_text": "Line 2 running smoothly. All machines within calibration spec. Yield steady at 96.5%."},
        {"note_id": "QC-011", "date": "2026-01-22", "plant": "Plant Southeast", "line_id": "Line 3", "inspector": "R. Gomez",
         "note_text": "Southeast Plant Line 3 is fine — yield at 95.8%. No calibration issues. This is only a Midwest Plant problem."},
        {"note_id": "QC-012", "date": "2026-02-05", "plant": "Plant Midwest", "line_id": "Line 3", "inspector": "S. Okafor",
         "note_text": "Received a batch from SUP-03 with lower material quality score than usual. However, the defect pattern on Line 3 is clearly mechanical (weld seam) not material (no surface cracking or brittleness). M-07 drift remains the primary issue."},
        {"note_id": "QC-013", "date": "2026-02-12", "plant": "Plant Midwest", "line_id": "Line 1", "inspector": "J. Kim",
         "note_text": "Line 1 continues excellent performance. Same SUP-03 material batch used here with zero quality issues, confirming the problem is machine-specific, not material-specific."},
        {"note_id": "QC-014", "date": "2026-02-15", "plant": "Plant Southeast", "line_id": "Line 1", "inspector": "R. Gomez",
         "note_text": "All Southeast lines performing within expected parameters. No yield deviation observed."},
    ]
    
    df_qc = pd.DataFrame(qc_notes)
    df_qc.to_csv(os.path.join(output_dir, "qc_inspector_notes.csv"), index=False)
    print(f"  qc_inspector_notes.csv: {len(df_qc)} rows")
    
    # =========================================================================
    # 6. maintenance_tickets.csv (unstructured free-text)
    # =========================================================================
    maint_tickets = [
        {"ticket_id": "MT-201", "date": "2025-05-20", "plant": "Plant Midwest", "line_id": "Line 2", "priority": "Low",
         "description": "Routine belt replacement on conveyor C-12. Scheduled during planned downtime. No production impact."},
        {"ticket_id": "MT-202", "date": "2025-07-14", "plant": "Plant Southeast", "line_id": "Line 1", "priority": "Medium",
         "description": "Pneumatic actuator on station S-04 showing intermittent pressure drops. Replaced O-ring seal. Resolved same shift."},
        {"ticket_id": "MT-203", "date": "2025-09-30", "plant": "Plant Midwest", "line_id": "Line 3", "priority": "Low",
         "description": "Annual preventive maintenance on M-07 weld station completed. All readings nominal. Drift at 0.2%."},
        {"ticket_id": "MT-204", "date": "2026-01-13", "plant": "Plant Midwest", "line_id": "Line 3", "priority": "Medium",
         "description": "M-07 weld station calibration drift alert triggered. Drift reading 1.2%, above the 1.0% threshold. Technician Rodriguez performed interim adjustment but drift re-appeared within 48 hours. Root cause suspected: worn servo motor encoder on weld arm axis 2."},
        {"ticket_id": "MT-205", "date": "2026-01-20", "plant": "Plant Midwest", "line_id": "Line 3", "priority": "High",
         "description": "URGENT: M-07 drift now at 2.1% and climbing. Interim calibration adjustments are not holding. QC reports increasing weld seam failures. Replacement servo encoder ordered from OEM — estimated 3-week lead time."},
        {"ticket_id": "MT-206", "date": "2026-01-27", "plant": "Plant Midwest", "line_id": "Line 3", "priority": "Critical",
         "description": "CRITICAL: M-07 calibration drift at 3.4%. First-pass yield on Line 3 has dropped to approximately 82%. Weld defect rate at housing seam station is 5x normal. Temporary manual inspection checkpoint installed downstream. Awaiting OEM encoder shipment."},
        {"ticket_id": "MT-207", "date": "2026-02-03", "plant": "Plant Midwest", "line_id": "Line 3", "priority": "Critical",
         "description": "M-07 drift at 4.1%. Production manager considering diverting Line 3 Model-A production to Line 1 temporarily. OEM part ETA updated to Feb 18. Cost impact estimated at $45k/week in rework and scrap."},
        {"ticket_id": "MT-208", "date": "2026-02-10", "plant": "Plant Midwest", "line_id": "Line 3", "priority": "Critical",
         "description": "M-07 drift peaked at 4.8%. Emergency decision: Line 3 production rate reduced by 20% to lower defect volume while awaiting encoder replacement. Inline QC checkpoint catching ~70% of defects before final assembly."},
        {"ticket_id": "MT-209", "date": "2025-11-05", "plant": "Plant Midwest", "line_id": "Line 1", "priority": "Low",
         "description": "Scheduled lubrication of all weld station servos. All readings within spec. No issues found."},
        {"ticket_id": "MT-210", "date": "2026-02-08", "plant": "Plant Southeast", "line_id": "Line 3", "priority": "Low",
         "description": "Routine inspection of Southeast Plant Line 3. All machines nominal. No calibration drift detected."},
    ]
    
    df_maint = pd.DataFrame(maint_tickets)
    df_maint.to_csv(os.path.join(output_dir, "maintenance_tickets.csv"), index=False)
    print(f"  maintenance_tickets.csv: {len(df_maint)} rows")
    
    print(f"\nAll 6 CSV files generated in: {output_dir}")
    print("Fiscal calendar note: fiscal_week = ISO week + 2 (modulo 52)")

if __name__ == "__main__":
    print("Generating Manufacturing Quality & Supply Chain benchmark...")
    generate_all(os.path.dirname(os.path.abspath(__file__)))
    print("Done!")
