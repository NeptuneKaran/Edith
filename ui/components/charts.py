"""
ui/components/charts.py
Interactive Plotly Visualizations for EDITH.
Ensures crisp, accessible, light-theme decision-grade styling with clear data grounding.
"""
import plotly.graph_objects as go
import pandas as pd

PLOT_THEME = {
    "paper_bgcolor": "#FFFFFF",
    "plot_bgcolor": "#FFFFFF",
    "font": {"color": "#1E293B", "family": "Inter, -apple-system, sans-serif", "size": 11},
    "margin": {"l": 45, "r": 20, "t": 35, "b": 35},
    "hoverlabel": {
        "bgcolor": "#0F172A",
        "bordercolor": "#334155",
        "font": {"family": "Inter, sans-serif", "size": 11, "color": "#FFFFFF"}
    }
}

def plot_expected_corridor(df: pd.DataFrame, kpi_name: str = "Monthly B2B Sales") -> go.Figure:
    """Plots historical KPI trend, rolling baseline, and shaded ±2σ expected corridor."""
    fig = go.Figure()
    
    # 1. Shaded Expected Corridor (±2σ)
    fig.add_trace(go.Scatter(
        x=df["week_label"],
        y=df["upper_corridor"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        name="Upper Corridor (+2σ)",
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=df["week_label"],
        y=df["lower_corridor"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(37, 99, 235, 0.08)", # Soft light blue
        name="Expected Band (±2.0σ)",
        hoverinfo="skip"
    ))
    
    # 2. Rolling Baseline
    fig.add_trace(go.Scatter(
        x=df["week_label"],
        y=df["baseline"],
        mode="lines",
        line=dict(color="#4F46E5", width=1.8, dash="dash"),
        name="Rolling 8-Wk Baseline",
        hovertemplate="Baseline: $%{y:,.0f}<extra></extra>"
    ))
    
    # 3. Actual Observed Series
    normal_points = df[~df["is_anomaly"]]
    fig.add_trace(go.Scatter(
        x=normal_points["week_label"],
        y=normal_points["value"],
        mode="lines+markers",
        line=dict(color="#0F172A", width=2.0),
        marker=dict(size=4, color="#0F172A"),
        name="Actual KPI Value",
        hovertemplate="%{x}<br>Actual: $%{y:,.0f}<extra></extra>"
    ))
    
    # 4. Highlight Anomalous Points in Red
    anom_points = df[df["is_anomaly"]]
    if not anom_points.empty:
        fig.add_trace(go.Scatter(
            x=anom_points["week_label"],
            y=anom_points["value"],
            mode="markers",
            marker=dict(size=11, color="#DC2626", symbol="circle", line=dict(color="#FFFFFF", width=2.0)),
            name="P1 Material Anomaly",
            hovertemplate="<b>ANOMALY BREACH</b><br>%{x}<br>Observed: $%{y:,.0f}<extra></extra>"
        ))
        
    fig.update_layout(
        **PLOT_THEME,
        height=320,
        title=dict(
            text=f"<b>{kpi_name} — 52-Week Trend vs Dynamic Corridor (±2.0σ)</b>",
            font=dict(size=13, color="#0F172A")
        ),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Weekly Timeline", tickangle=-30, tickfont=dict(color="#475569")),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Value ($)", tickfont=dict(color="#475569")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10, color="#334155"))
    )
    return fig

def plot_waterfall_contribution(df_breakdown: pd.DataFrame, dimension_col: str, title: str) -> go.Figure:
    """Plots dimensional variance breakdown showing individual contribution shares."""
    df_sorted = df_breakdown.sort_values("delta_value", ascending=True)
    
    colors = ["#DC2626" if val < 0 else "#16A34A" for val in df_sorted["delta_value"]]
    
    fig = go.Figure(go.Bar(
        x=df_sorted["delta_value"],
        y=df_sorted[dimension_col],
        orientation="h",
        marker=dict(color=colors, line=dict(color="#CBD5E1", width=1)),
        text=[f"{val:+,.0f} ({pct:.1f}%)" for val, pct in zip(df_sorted["delta_value"], df_sorted["contribution_pct"])],
        textposition="auto",
        textfont=dict(color="#0F172A", size=11, family="Inter, sans-serif"),
        hovertemplate="<b>%{y}</b><br>Delta: $%{x:+,.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        **PLOT_THEME,
        height=220,
        title=dict(
            text=f"<b>{title} (Variance Contribution Share)</b>",
            font=dict(size=12, color="#0F172A")
        ),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Revenue Variance ($)", tickfont=dict(color="#475569")),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", tickfont=dict(color="#334155"))
    )
    return fig

def plot_did_cohort(df_cohort: pd.DataFrame) -> go.Figure:
    """Plots Difference-in-Differences cohort trajectory comparing treated vs control cohorts."""
    fig = go.Figure()
    
    # Enterprise (Treated)
    if "Enterprise" in df_cohort.columns:
        fig.add_trace(go.Scatter(
            x=df_cohort["week_label"],
            y=df_cohort["Enterprise"],
            mode="lines+markers",
            line=dict(color="#DC2626", width=2.5),
            marker=dict(size=5),
            name="Treated: Enterprise (+12% Price Hike)",
            hovertemplate="Enterprise: $%{y:,.0f}<extra></extra>"
        ))
        
    # Mid-Market (Control)
    if "Mid-Market" in df_cohort.columns:
        fig.add_trace(go.Scatter(
            x=df_cohort["week_label"],
            y=df_cohort["Mid-Market"],
            mode="lines+markers",
            line=dict(color="#16A34A", width=2.0, dash="dash"),
            marker=dict(size=5),
            name="Control: Mid-Market (Un-Hiked Price)",
            hovertemplate="Mid-Market: $%{y:,.0f}<extra></extra>"
        ))
        
    fig.add_vline(x="2026-W06", line_width=1.2, line_dash="dot", line_color="#D97706", annotation_text="Price Hike (W06)", annotation_font_size=9)
    fig.add_vline(x="2026-W07", line_width=1.2, line_dash="dot", line_color="#2563EB", annotation_text="Competitor Promo (W07)", annotation_font_size=9)
    
    fig.update_layout(
        **PLOT_THEME,
        height=260,
        title=dict(
            text="<b>Difference-in-Differences: Treated vs Control Cohorts</b>",
            font=dict(size=12, color="#0F172A")
        ),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Weekly Timeline", tickfont=dict(color="#475569")),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Revenue ($)", tickfont=dict(color="#475569")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10, color="#334155"))
    )
    return fig

def plot_simulation_trajectory(trajectory_df: pd.DataFrame) -> go.Figure:
    """Plots 8-week projected counterfactual recovery trajectories."""
    fig = go.Figure()
    
    # Baseline target
    fig.add_trace(go.Scatter(
        x=trajectory_df["projection_week"],
        y=trajectory_df["Baseline Target"],
        mode="lines",
        line=dict(color="#4F46E5", width=1.8, dash="dash"),
        name="Baseline Target ($1.40M)",
        hovertemplate="Baseline: $%{y:,.0f}<extra></extra>"
    ))
    
    # Do-Nothing Outlook
    fig.add_trace(go.Scatter(
        x=trajectory_df["projection_week"],
        y=trajectory_df["Do-Nothing Outlook"],
        mode="lines",
        line=dict(color="#DC2626", width=1.8, dash="dot"),
        name="Do-Nothing Outlook (Sustained Drop)",
        hovertemplate="Do-Nothing: $%{y:,.0f}<extra></extra>"
    ))
    
    # Simulated Recovery Curve
    fig.add_trace(go.Scatter(
        x=trajectory_df["projection_week"],
        y=trajectory_df["Simulated Scenario"],
        mode="lines+markers",
        line=dict(color="#16A34A", width=3.0),
        marker=dict(size=6, color="#16A34A"),
        name="Simulated Recovery Trajectory",
        hovertemplate="Simulated: $%{y:,.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        **PLOT_THEME,
        height=300,
        title=dict(
            text="<b>Projected 8-Week Revenue Recovery Trajectory</b>",
            font=dict(size=13, color="#0F172A")
        ),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Forward Horizon (Weeks)", tickfont=dict(color="#475569")),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Weekly Revenue ($)", tickfont=dict(color="#475569")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10, color="#334155"))
    )
    return fig
