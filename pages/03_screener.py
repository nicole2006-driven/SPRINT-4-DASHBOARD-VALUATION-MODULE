import sys
from pathlib import Path
import streamlit as st
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.dashboard.utils.db import (
    get_companies, get_sectors, get_ratios, get_market_cap, get_analysis
)

st.set_page_config(page_title="Stock Screener | Nifty 100 Analytics", layout="wide")
st.title("🔎 Nifty 100 Multi-Metric Stock Screener")

# Build unified latest-year master dataframe
companies = get_companies()[["company_id", "company_name"]]
sectors = get_sectors()[["company_id", "broad_sector"]]
ratios = get_ratios().sort_values("year").groupby("company_id", as_index=False).last()
mcap = get_market_cap().sort_values("year").groupby("company_id", as_index=False).last()
analysis = get_analysis()[["company_id", "sales_cagr_5yr", "pat_cagr_5yr"]]

df = (
    companies
    .merge(sectors, on="company_id", how="left")
    .merge(ratios[[
        "company_id", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
        "operating_profit_margin_pct", "interest_coverage"
    ]], on="company_id", how="left")
    .merge(mcap[["company_id", "pe_ratio", "pb_ratio", "dividend_yield_pct"]], on="company_id", how="left")
    .merge(analysis, on="company_id", how="left")
)

# Composite score
df["composite_score"] = (
    df["return_on_equity_pct"].rank(pct=True).fillna(0.5) * 35 +
    df["operating_profit_margin_pct"].rank(pct=True).fillna(0.5) * 25 +
    (1 - df["debt_to_equity"].rank(pct=True)).fillna(0.5) * 20 +
    df["sales_cagr_5yr"].rank(pct=True).fillna(0.5) * 20
).round(1)

# Default slider state
DEFAULTS = {
    "roe_min": -50.0,
    "de_max": 15.0,
    "fcf_min": -50000.0,
    "rev_cagr_min": -50.0,
    "pat_cagr_min": -50.0,
    "opm_min": -50.0,
    "pe_max": 250.0,
    "pb_max": 100.0,
    "div_min": 0.0,
    "icr_min": -10.0,
}

PRESETS = {
    "Quality": {"roe_min": 18.0, "de_max": 0.5, "fcf_min": 500.0, "rev_cagr_min": 8.0, "pat_cagr_min": 8.0, "opm_min": 15.0, "pe_max": 250.0, "pb_max": 100.0, "div_min": 0.0, "icr_min": 5.0},
    "Value": {"roe_min": 10.0, "de_max": 1.5, "fcf_min": 0.0, "rev_cagr_min": -50.0, "pat_cagr_min": -50.0, "opm_min": 5.0, "pe_max": 22.0, "pb_max": 3.5, "div_min": 1.0, "icr_min": 2.0},
    "Growth": {"roe_min": 12.0, "de_max": 2.0, "fcf_min": -50000.0, "rev_cagr_min": 15.0, "pat_cagr_min": 15.0, "opm_min": 10.0, "pe_max": 250.0, "pb_max": 100.0, "div_min": 0.0, "icr_min": 2.0},
    "Dividend": {"roe_min": 10.0, "de_max": 1.5, "fcf_min": 200.0, "rev_cagr_min": -50.0, "pat_cagr_min": -50.0, "opm_min": 5.0, "pe_max": 250.0, "pb_max": 100.0, "div_min": 2.0, "icr_min": 2.0},
    "Debt-Free": {"roe_min": 10.0, "de_max": 0.05, "fcf_min": 0.0, "rev_cagr_min": -50.0, "pat_cagr_min": -50.0, "opm_min": 5.0, "pe_max": 250.0, "pb_max": 100.0, "div_min": 0.0, "icr_min": 0.0},
    "Turnaround": {"roe_min": 5.0, "de_max": 3.0, "fcf_min": 0.0, "rev_cagr_min": 5.0, "pat_cagr_min": 10.0, "opm_min": 5.0, "pe_max": 40.0, "pb_max": 10.0, "div_min": 0.0, "icr_min": 1.5},
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# 6 Preset Buttons
st.markdown("**Quick Strategy Presets:**")
bcols = st.columns(7)
for idx, (preset_name, preset_vals) in enumerate(PRESETS.items()):
    if bcols[idx].button(preset_name, use_container_width=True):
        for k, v in preset_vals.items():
            st.session_state[k] = v
if bcols[6].button("Reset All", use_container_width=True):
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

# 10 Metric Sliders in Sidebar
st.sidebar.header("Filter Criteria")
roe_min = st.sidebar.slider("ROE Min (%)", -50.0, 60.0, key="roe_min")
de_max = st.sidebar.slider("D/E Max", 0.0, 15.0, key="de_max")
fcf_min = st.sidebar.slider("FCF Min (₹ Cr)", -50000.0, 50000.0, step=500.0, key="fcf_min")
rev_cagr_min = st.sidebar.slider("Revenue CAGR 5Y Min (%)", -50.0, 50.0, key="rev_cagr_min")
pat_cagr_min = st.sidebar.slider("PAT CAGR 5Y Min (%)", -50.0, 50.0, key="pat_cagr_min")
opm_min = st.sidebar.slider("OPM Min (%)", -50.0, 80.0, key="opm_min")
pe_max = st.sidebar.slider("P/E Max", 1.0, 250.0, key="pe_max")
pb_max = st.sidebar.slider("P/B Max", 0.5, 100.0, key="pb_max")
div_min = st.sidebar.slider("Dividend Yield Min (%)", 0.0, 15.0, step=0.25, key="div_min")
icr_min = st.sidebar.slider("ICR Min", -10.0, 100.0, key="icr_min")

# Apply filters safely (handle NaNs without crashing at extremes)
mask = (
    (df["return_on_equity_pct"].fillna(-999) >= roe_min) &
    (df["debt_to_equity"].fillna(0) <= de_max) &
    (df["free_cash_flow_cr"].fillna(-999999) >= fcf_min) &
    (df["sales_cagr_5yr"].fillna(-999) >= rev_cagr_min) &
    (df["pat_cagr_5yr"].fillna(-999) >= pat_cagr_min) &
    (df["operating_profit_margin_pct"].fillna(-999) >= opm_min) &
    (df["pe_ratio"].fillna(0) <= pe_max) &
    (df["pb_ratio"].fillna(0) <= pb_max) &
    (df["dividend_yield_pct"].fillna(0) >= div_min) &
    (df["interest_coverage"].fillna(999) >= icr_min)
)

res = df[mask].sort_values("composite_score", ascending=False).copy()
res_display = res.rename(columns={
    "company_id": "company_id",
    "company_name": "name",
    "broad_sector": "sector",
    "composite_score": "composite_score",
    "return_on_equity_pct": "ROE_%",
    "debt_to_equity": "D_E",
    "free_cash_flow_cr": "FCF_Cr",
    "sales_cagr_5yr": "Rev_CAGR_5Y_%",
    "pat_cagr_5yr": "PAT_CAGR_5Y_%",
    "operating_profit_margin_pct": "OPM_%",
    "pe_ratio": "P_E",
    "pb_ratio": "P_B",
    "dividend_yield_pct": "Div_Yield_%",
    "interest_coverage": "ICR"
})

st.subheader(f"{len(res_display)} companies match your filters")

csv_bytes = res_display.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Screener Results (CSV)",
    data=csv_bytes,
    file_name="nifty100_screener_results.csv",
    mime="text/csv"
)

st.dataframe(res_display, use_container_width=True, hide_index=True)