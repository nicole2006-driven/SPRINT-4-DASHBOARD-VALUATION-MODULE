import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.dashboard.utils.db import (
    get_companies, get_sectors, get_ratios, get_market_cap, get_pl
)

st.set_page_config(page_title="Sector Analysis | Nifty 100 Analytics", layout="wide")
st.title("🏭 Sector & Sub-Sector Analysis")

sectors = get_sectors()
all_sectors = sorted(sectors["broad_sector"].dropna().unique().tolist())
selected_sector = st.selectbox("Select Broad Sector", options=all_sectors)

companies = get_companies()[["company_id", "company_name"]]
ratios = get_ratios().sort_values("year").groupby("company_id", as_index=False).last()
mcap = get_market_cap().sort_values("year").groupby("company_id", as_index=False).last()
pl = get_pl()
pl_latest = pl[~pl["year"].astype(str).str.upper().str.contains("TTM")].groupby("company_id", as_index=False).last()

df = (
    sectors[sectors["broad_sector"] == selected_sector]
    .merge(companies, on="company_id", how="left")
    .merge(ratios[["company_id", "return_on_equity_pct", "operating_profit_margin_pct", "net_profit_margin_pct", "debt_to_equity"]], on="company_id", how="left")
    .merge(mcap[["company_id", "market_cap_crore", "pe_ratio"]], on="company_id", how="left")
    .merge(pl_latest[["company_id", "sales"]], on="company_id", how="left")
)

df["market_cap_clean"] = df["market_cap_crore"].fillna(1000).clip(lower=100)
df["sales_clean"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0)

st.subheader(f"{selected_sector} — Revenue vs. ROE (Bubble Size = Market Cap)")
fig_bubble = px.scatter(
    df.dropna(subset=["return_on_equity_pct"]),
    x="sales_clean",
    y="return_on_equity_pct",
    size="market_cap_clean",
    color="sub_sector",
    hover_name="company_name",
    hover_data={"company_id": True, "market_cap_crore": ":,.0f", "pe_ratio": ":.1f", "market_cap_clean": False},
    labels={
        "sales_clean": "Latest Annual Revenue (₹ Cr)",
        "return_on_equity_pct": "ROE (%)",
        "sub_sector": "Sub-Sector"
    },
    size_max=55,
    height=450
)
fig_bubble.update_layout(margin=dict(t=20, b=30, l=20, r=20))
st.plotly_chart(fig_bubble, use_container_width=True)

st.divider()

# Sector Median KPI Bar Chart across all 11 sectors for comparison
st.subheader("Sector Median KPIs Across All Broad Sectors")
full_df = (
    sectors
    .merge(ratios[["company_id", "return_on_equity_pct", "operating_profit_margin_pct", "net_profit_margin_pct"]], on="company_id", how="left")
    .merge(mcap[["company_id", "pe_ratio"]], on="company_id", how="left")
)

sec_med = full_df.groupby("broad_sector", as_index=False).agg({
    "return_on_equity_pct": "median",
    "operating_profit_margin_pct": "median",
    "net_profit_margin_pct": "median",
    "pe_ratio": "median"
}).rename(columns={
    "broad_sector": "Sector",
    "return_on_equity_pct": "Median ROE (%)",
    "operating_profit_margin_pct": "Median OPM (%)",
    "net_profit_margin_pct": "Median NPM (%)",
    "pe_ratio": "Median P/E"
})

med_melted = sec_med.melt(id_vars="Sector", var_name="KPI", value_name="Median Value")
fig_bar = px.bar(
    med_melted,
    x="Sector",
    y="Median Value",
    color="KPI",
    barmode="group",
    height=420
)
fig_bar.update_layout(margin=dict(t=20, b=40, l=20, r=20))
st.plotly_chart(fig_bar, use_container_width=True)