import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.dashboard.utils.db import (
    get_companies, get_sectors, get_ratios, get_pl, get_analysis, get_prosandcons
)

st.set_page_config(page_title="Company Profile | Nifty 100 Analytics", layout="wide")
st.title("🏢 Company 360° Profile")

companies = get_companies()
sectors = get_sectors()
analysis = get_analysis()

# Search box + autocomplete dropdown
search_query = st.text_input("Search by Company Name or Ticker", placeholder="e.g., TCS, HDFC, Reliance...")

filtered_comp = companies.copy()
if search_query.strip():
    q = search_query.strip().lower()
    filtered_comp = companies[
        companies["company_id"].str.lower().str.contains(q, na=False) |
        companies["company_name"].str.lower().str.contains(q, na=False)
    ]

if filtered_comp.empty:
    st.warning("Ticker not found — please try another")
    st.stop()

options = [f"{row['company_id']} — {row['company_name']}" for _, row in filtered_comp.iterrows()]
selected_option = st.selectbox("Select Matching Company", options=options)
ticker = selected_option.split(" — ")[0].strip()

comp_row = companies[companies["company_id"] == ticker].iloc[0]
sec_match = sectors[sectors["company_id"] == ticker]
broad_sec = sec_match["broad_sector"].iloc[0] if not sec_match.empty else "N/A"
sub_sec = sec_match["sub_sector"].iloc[0] if not sec_match.empty else "N/A"

# Company Card
with st.container(border=True):
    st.subheader(f"{comp_row['company_name']} ({ticker})")
    st.caption(f"**Sector:** {broad_sec}  |  **Sub-Sector:** {sub_sec}  |  **NSE Ticker:** {ticker}")
    about = comp_row.get("about_company", "")
    st.write(about if pd.notna(about) and str(about).strip() else "Company description not available.")

# Load historical ratios & P&L
ratios_df = get_ratios(ticker=ticker).sort_values("year")
pl_df = get_pl(ticker=ticker)
pl_hist = pl_df[~pl_df["year"].astype(str).str.upper().str.contains("TTM")].tail(10)

if len(ratios_df) < 10:
    st.info(f"Note: Partial historical data available ({len(ratios_df)} years on record for {ticker}).")

latest_r = ratios_df.iloc[-1] if not ratios_df.empty else pd.Series(dtype="object")
an_match = analysis[analysis["company_id"] == ticker]
rev_cagr_5y = an_match["sales_cagr_5yr"].iloc[0] if not an_match.empty else None

def fmt(val, suffix=""):
    return f"{val:.2f}{suffix}" if pd.notna(val) else "N/A"

# 6 KPI Tiles
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("ROE", fmt(latest_r.get("return_on_equity_pct", comp_row.get("roe_percentage")), "%"))
k2.metric("ROCE", fmt(comp_row.get("roce_percentage"), "%"))
k3.metric("Net Profit Margin", fmt(latest_r.get("net_profit_margin_pct"), "%"))
k4.metric("Debt / Equity", fmt(latest_r.get("debt_to_equity")))
k5.metric("Revenue CAGR (5Y)", fmt(rev_cagr_5y, "%"))
k6.metric("FCF (Latest Yr)", fmt(latest_r.get("free_cash_flow_cr"), " Cr"))

st.divider()

# Charts
ch1, ch2 = st.columns(2)

with ch1:
    st.subheader("10-Year Revenue & Net Profit (₹ Cr)")
    if not pl_hist.empty:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=pl_hist["year"].astype(str), y=pl_hist["sales"], name="Revenue (Sales)"))
        fig_bar.add_trace(go.Bar(x=pl_hist["year"].astype(str), y=pl_hist["net_profit"], name="Net Profit"))
        fig_bar.update_layout(barmode="group", height=380, margin=dict(t=30, b=30, l=20, r=20), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No P&L data available.")

with ch2:
    st.subheader("ROE & Margin Trend Over Time (%)")
    r_10 = ratios_df.tail(10)
    if not r_10.empty:
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(
            go.Scatter(x=r_10["year"].astype(str), y=r_10["return_on_equity_pct"], name="ROE (%)", mode="lines+markers"),
            secondary_y=False
        )
        # Plot Operating Profit Margin alongside ROE (and show latest ROCE reference)
        fig_dual.add_trace(
            go.Scatter(x=r_10["year"].astype(str), y=r_10["operating_profit_margin_pct"], name="OPM / ROCE Proxy (%)", mode="lines+markers"),
            secondary_y=True
        )
        fig_dual.update_yaxes(title_text="ROE (%)", secondary_y=False)
        fig_dual.update_yaxes(title_text="OPM (%)", secondary_y=True)
        fig_dual.update_layout(height=380, margin=dict(t=30, b=30, l=20, r=20), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig_dual, use_container_width=True)
    else:
        st.info("No ratio history available.")

# Pros & Cons Badges
st.subheader("Strengths & Watchouts (Pros & Cons)")
pc_df = get_prosandcons(ticker=ticker)
col_pro, col_con = st.columns(2)

with col_pro:
    st.markdown("**Pros**")
    pros = pc_df["pros"].dropna().tolist() if not pc_df.empty else []
    if pros:
        for p in pros:
            if str(p).strip():
                st.success(f"✅ {p}")
    else:
        st.caption("No recorded pros for this ticker.")

with col_con:
    st.markdown("**Cons**")
    cons = pc_df["cons"].dropna().tolist() if not pc_df.empty else []
    if cons:
        for c in cons:
            if str(c).strip():
                st.error(f"❌ {c}")
    else:
        st.caption("No recorded cons for this ticker.")

