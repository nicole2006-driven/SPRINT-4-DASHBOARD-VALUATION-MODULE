import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_market_cap, get_sectors, get_analysis
)

st.set_page_config(page_title="Home | Nifty 100 Analytics", layout="wide")
st.title("🏠 Nifty 100 Market Overview")

# Sidebar year selector (2019 to 2024)
selected_year = st.sidebar.selectbox(
    "Select Financial Year",
    options=[2024, 2023, 2022, 2021, 2020, 2019],
    index=0
)

companies = get_companies()
ratios_yr = get_ratios(year=selected_year)
mcap_yr = get_market_cap(year=selected_year)
sectors = get_sectors()
analysis = get_analysis()

# Compute 6 summary KPIs
avg_roe = ratios_yr["return_on_equity_pct"].dropna().mean()
med_pe = mcap_yr["pe_ratio"].dropna().median()
med_de = ratios_yr["debt_to_equity"].dropna().median()
total_companies = len(companies)
med_rev_cagr = analysis["sales_cagr_5yr"].dropna().median()
debt_free_count = int((ratios_yr["debt_to_equity"].fillna(999) <= 0.05).sum())

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Average ROE", f"{avg_roe:.2f}%" if pd.notna(avg_roe) else "N/A")
c2.metric("Median P/E", f"{med_pe:.2f}x" if pd.notna(med_pe) else "N/A")
c3.metric("Median D/E", f"{med_de:.2f}" if pd.notna(med_de) else "N/A")
c4.metric("Total Companies", f"{total_companies}")
c5.metric("Median Rev CAGR (5Y)", f"{med_rev_cagr:.2f}%" if pd.notna(med_rev_cagr) else "N/A")
c6.metric("Debt-Free Companies", f"{debt_free_count}")

st.divider()

col_left, col_right = st.columns([1.1, 1])

with col_left:
    st.subheader("Sector Breakdown (11 Broad Sectors)")
    sec_counts = sectors.groupby("broad_sector", as_index=False)["company_id"].count()
    sec_counts.columns = ["Sector", "Companies"]
    fig_donut = px.pie(
        sec_counts,
        names="Sector",
        values="Companies",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_donut.update_traces(textposition="inside", textinfo="value+percent")
    fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=420)
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.subheader(f"Top 5 Companies by Composite Quality Score ({selected_year})")
    # Compute composite quality score from ROE, ROCE/OPM, Low D/E, and 5Y Growth
    qual = companies[["company_id", "company_name", "roce_percentage"]].merge(
        sectors[["company_id", "broad_sector"]], on="company_id", how="left"
    ).merge(
        ratios_yr[["company_id", "return_on_equity_pct", "operating_profit_margin_pct", "debt_to_equity"]],
        on="company_id", how="left"
    ).merge(
        analysis[["company_id", "sales_cagr_5yr", "pat_cagr_5yr"]],
        on="company_id", how="left"
    )

    # Normalized percentile rank composite score (0-100)
    s_roe = qual["return_on_equity_pct"].rank(pct=True).fillna(0.5)
    s_opm = qual["operating_profit_margin_pct"].rank(pct=True).fillna(0.5)
    s_de = (1 - qual["debt_to_equity"].rank(pct=True)).fillna(0.5)
    s_growth = qual["sales_cagr_5yr"].rank(pct=True).fillna(0.5)
    qual["Composite Score"] = ((s_roe * 0.35 + s_opm * 0.25 + s_de * 0.20 + s_growth * 0.20) * 100).round(1)

    top5 = (
        qual.sort_values("Composite Score", ascending=False)
        .head(5)[["company_id", "company_name", "broad_sector", "return_on_equity_pct", "debt_to_equity", "Composite Score"]]
        .rename(columns={
            "company_id": "Ticker",
            "company_name": "Company",
            "broad_sector": "Sector",
            "return_on_equity_pct": "ROE (%)",
            "debt_to_equity": "D/E"
        })
    )
    st.dataframe(top5, use_container_width=True, hide_index=True)