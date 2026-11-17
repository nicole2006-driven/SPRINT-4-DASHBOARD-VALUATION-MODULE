import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.dashboard.utils.db import (
    get_peers, get_companies, get_ratios, get_market_cap, get_analysis
)

st.set_page_config(page_title="Peer Comparison | Nifty 100 Analytics", layout="wide")
st.title("⚖️ Peer Group Comparison")

peers_all = get_peers()
groups = sorted(peers_all["peer_group_name"].dropna().unique().tolist())

c1, c2 = st.columns(2)
selected_group = c1.selectbox("Select Peer Group (11 Groups)", options=groups)

group_df = peers_all[peers_all["peer_group_name"] == selected_group].copy()
companies = get_companies()[["company_id", "company_name", "roce_percentage"]]
ratios = get_ratios().sort_values("year").groupby("company_id", as_index=False).last()
mcap = get_market_cap().sort_values("year").groupby("company_id", as_index=False).last()
analysis = get_analysis()[["company_id", "sales_cagr_5yr"]]

merged = (
    group_df
    .merge(companies, on="company_id", how="left")
    .merge(ratios[[
        "company_id", "return_on_equity_pct", "net_profit_margin_pct",
        "operating_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr"
    ]], on="company_id", how="left")
    .merge(mcap[["company_id", "pe_ratio", "pb_ratio"]], on="company_id", how="left")
    .merge(analysis, on="company_id", how="left")
)

# Default to benchmark company if marked
bench_rows = merged[merged["is_benchmark"].astype(str).str.lower().isin(["true", "1", "yes"])]
default_idx = 0
if not bench_rows.empty:
    bench_id = bench_rows.iloc[0]["company_id"]
    ids = merged["company_id"].tolist()
    if bench_id in ids:
        default_idx = ids.index(bench_id)

selected_ticker = c2.selectbox(
    "Select Company to Compare Against Peer Average",
    options=merged["company_id"].tolist(),
    index=default_idx
)

# 8 Radar Metrics
radar_cols = [
    "return_on_equity_pct", "roce_percentage", "net_profit_margin_pct",
    "operating_profit_margin_pct", "sales_cagr_5yr", "pe_ratio", "pb_ratio", "debt_to_equity"
]
radar_labels = ["ROE %", "ROCE %", "NPM %", "OPM %", "Rev CAGR 5Y %", "P/E", "P/B", "D/E"]

# Normalize 0-100 within peer group for clean visual scale on Scatterpolar
norm_df = merged[radar_cols].copy()
for col in radar_cols:
    col_min, col_max = norm_df[col].min(), norm_df[col].max()
    if pd.notna(col_min) and pd.notna(col_max) and col_max > col_min:
        norm_df[col] = ((norm_df[col] - col_min) / (col_max - col_min)) * 100
    else:
        norm_df[col] = 50.0

comp_idx = merged[merged["company_id"] == selected_ticker].index[0]
comp_vals = norm_df.loc[comp_idx, radar_cols].fillna(0).tolist()
peer_avg_vals = norm_df[radar_cols].mean().fillna(0).tolist()

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=comp_vals + [comp_vals[0]],
    theta=radar_labels + [radar_labels[0]],
    fill="toself",
    name=selected_ticker
))
fig_radar.add_trace(go.Scatterpolar(
    r=peer_avg_vals + [peer_avg_vals[0]],
    theta=radar_labels + [radar_labels[0]],
    fill="toself",
    name=f"{selected_group} Avg"
))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    height=440,
    margin=dict(t=30, b=30, l=40, r=40)
)
st.plotly_chart(fig_radar, use_container_width=True)

# Side-by-Side KPI Table with highlighted selected/benchmark row
st.subheader("Peer Group Side-by-Side KPIs")
table_df = merged[[
    "company_id", "company_name", "return_on_equity_pct", "roce_percentage",
    "net_profit_margin_pct", "operating_profit_margin_pct", "debt_to_equity",
    "pe_ratio", "pb_ratio", "free_cash_flow_cr", "sales_cagr_5yr"
]].rename(columns={
    "company_id": "Ticker",
    "company_name": "Company",
    "return_on_equity_pct": "ROE (%)",
    "roce_percentage": "ROCE (%)",
    "net_profit_margin_pct": "NPM (%)",
    "operating_profit_margin_pct": "OPM (%)",
    "debt_to_equity": "D/E",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B",
    "free_cash_flow_cr": "FCF (Cr)",
    "sales_cagr_5yr": "Rev CAGR 5Y (%)"
})

def highlight_benchmark(row):
    if row["Ticker"] == selected_ticker:
        return ["background-color: #1f4e78; color: white; font-weight: bold"] * len(row)
    return [""] * len(row)

st.dataframe(table_df.style.apply(highlight_benchmark, axis=1), use_container_width=True, hide_index=True)