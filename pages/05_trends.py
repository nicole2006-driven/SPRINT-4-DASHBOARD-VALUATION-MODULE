import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_cf

st.set_page_config(page_title="Trend Analysis | Nifty 100 Analytics", layout="wide")
st.title("📈 10-Year Multi-Metric Trend Analysis")

companies = get_companies()
options = [f"{r['company_id']} — {r['company_name']}" for _, r in companies.iterrows()]
selected = st.selectbox("Search & Select Company", options=options)
ticker = selected.split(" — ")[0].strip()

# Merge annual ratios, P&L, and Cash Flow on integer year
ratios = get_ratios(ticker=ticker).copy()
ratios["year_int"] = pd.to_numeric(ratios["year"], errors="coerce")

pl = get_pl(ticker=ticker).copy()
pl = pl[~pl["year"].astype(str).str.upper().str.contains("TTM")]
pl["year_int"] = pl["year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)

cf = get_cf(ticker=ticker).copy()
cf["year_int"] = cf["year"].astype(str).str.extract(r"(\d{4})")[0].astype(float)

merged = ratios.merge(
    pl[["year_int", "sales", "operating_profit", "net_profit", "eps"]],
    on="year_int",
    how="outer"
).merge(
    cf[["year_int", "operating_activity", "investing_activity", "financing_activity"]],
    on="year_int",
    how="left"
).dropna(subset=["year_int"]).sort_values("year_int").tail(10)

if len(merged) < 10:
    st.info(f"Note: Partial historical data available ({len(merged)} years on record for {ticker}).")

METRIC_MAP = {
    "Revenue / Sales (₹ Cr)": "sales",
    "Net Profit (₹ Cr)": "net_profit",
    "Operating Profit (₹ Cr)": "operating_profit",
    "Free Cash Flow (₹ Cr)": "free_cash_flow_cr",
    "ROE (%)": "return_on_equity_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "Operating Profit Margin (%)": "operating_profit_margin_pct",
    "Debt / Equity": "debt_to_equity",
    "EPS (₹)": "eps",
    "Cash from Operations (₹ Cr)": "operating_activity"
}

chosen_labels = st.multiselect(
    "Select up to 3 Metrics to Overlay",
    options=list(METRIC_MAP.keys()),
    default=["Revenue / Sales (₹ Cr)", "Net Profit (₹ Cr)"],
    max_selections=3
)

if not chosen_labels:
    st.warning("Please select at least 1 metric above.")
    st.stop()

fig = make_subplots(specs=[[{"secondary_y": True}]])
x_years = merged["year_int"].astype(int).astype(str)

for idx, label in enumerate(chosen_labels):
    col = METRIC_MAP[label]
    vals = pd.to_numeric(merged[col], errors="coerce")
    yoy = vals.pct_change() * 100.0
    text_labels = [f"{y:+.1f}%" if pd.notna(y) else "" for y in yoy]

    # Use secondary axis if metric scale differs (e.g. % or ratio vs Cr)
    use_sec = (idx > 0) and ("(%)" in label or "Equity" in label or "EPS" in label)

    fig.add_trace(
        go.Scatter(
            x=x_years,
            y=vals,
            name=label,
            mode="lines+markers+text",
            text=text_labels,
            textposition="top center",
            textfont=dict(size=10)
        ),
        secondary_y=use_sec
    )

fig.update_layout(
    title=f"{ticker} — 10-Year Trajectory with YoY % Change Annotations",
    height=480,
    margin=dict(t=50, b=30, l=30, r=30),
    legend=dict(orientation="h", y=1.12)
)
st.plotly_chart(fig, use_container_width=True)