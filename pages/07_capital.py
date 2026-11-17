import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.dashboard.utils.db import (
    get_companies, get_sectors, get_ratios, get_market_cap, get_cf
)

st.set_page_config(page_title="Capital Allocation | Nifty 100 Analytics", layout="wide")
st.title("🧭 Capital Allocation Map (8 Patterns)")

companies = get_companies()[["company_id", "company_name"]]
sectors = get_sectors()[["company_id", "broad_sector"]]
ratios = get_ratios().sort_values("year").groupby("company_id", as_index=False).last()
mcap = get_market_cap().sort_values("year").groupby("company_id", as_index=False).last()
cf = get_cf().groupby("company_id", as_index=False).last()

df = (
    companies
    .merge(sectors, on="company_id", how="left")
    .merge(ratios[[
        "company_id", "return_on_equity_pct", "debt_to_equity",
        "free_cash_flow_cr", "capex_cr", "dividend_payout_ratio_pct", "cash_from_operations_cr"
    ]], on="company_id", how="left")
    .merge(mcap[["company_id", "market_cap_crore"]], on="company_id", how="left")
    .merge(cf[["company_id", "operating_activity", "investing_activity", "financing_activity"]], on="company_id", how="left")
)

def classify_capital_pattern(row):
    """Classifies all 92 companies into 8 distinct capital allocation archetypes."""
    roe = row.get("return_on_equity_pct", 0) or 0
    de = row.get("debt_to_equity", 0) or 0
    fcf = row.get("free_cash_flow_cr", 0) or 0
    capex = abs(row.get("capex_cr", 0) or 0)
    cfo = row.get("cash_from_operations_cr", row.get("operating_activity", 0)) or 0
    div_pay = row.get("dividend_payout_ratio_pct", 0) or 0
    sector = str(row.get("broad_sector", ""))

    if "Financial" in sector or "Bank" in sector:
        return "1. Financial Balance-Sheet Compounders" if roe >= 14 else "2. Financial Credit Rebuilders"
    if fcf > 0 and roe >= 20 and div_pay >= 35:
        return "3. Cash-Cow Dividend Aristocrats"
    if fcf > 0 and roe >= 18 and de <= 0.3:
        return "4. Asset-Light High-ROE Compounders"
    if cfo > 0 and capex > (0.5 * cfo) and roe >= 12:
        return "5. High-Reinvestment Capex Builders"
    if cfo > 0 and fcf < 0:
        return "6. Heavy Infrastructure / Expansion Spenders"
    if de > 0.8 and cfo > 0:
        return "7. Deleveraging / Debt-Servicing Operators"
    return "8. Turnaround / Working-Capital Absorbers"

df["capital_pattern"] = df.apply(classify_capital_pattern, axis=1)
df["mcap_size"] = df["market_cap_crore"].fillna(5000).clip(lower=500)

fig_tree = px.treemap(
    df,
    path=[px.Constant("Nifty 100 (92 Companies)"), "capital_pattern", "company_id"],
    values="mcap_size",
    color="capital_pattern",
    hover_data={"company_name": True, "return_on_equity_pct": ":.1f", "debt_to_equity": ":.2f", "free_cash_flow_cr": ":,.0f", "mcap_size": False},
    height=500
)
fig_tree.update_layout(margin=dict(t=25, b=10, l=10, r=10))

event = st.plotly_chart(fig_tree, use_container_width=True, on_select="rerun", selection_mode="points")

# Interactive drill-down by click or dropdown
patterns = sorted(df["capital_pattern"].unique().tolist())
clicked_pattern = None
if event and event.selection and event.selection.points:
    pt = event.selection.points[0]
    pt_id = pt.get("id", "")
    for p in patterns:
        if p in str(pt_id):
            clicked_pattern = p
            break

default_index = patterns.index(clicked_pattern) if clicked_pattern in patterns else 0
selected_pattern = st.selectbox(
    "Inspect Companies in Capital Allocation Pattern (or click a tile above)",
    options=patterns,
    index=default_index
)

sub_df = df[df["capital_pattern"] == selected_pattern][[
    "company_id", "company_name", "broad_sector", "market_cap_crore",
    "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "dividend_payout_ratio_pct"
]].rename(columns={
    "company_id": "Ticker",
    "company_name": "Company",
    "broad_sector": "Sector",
    "market_cap_crore": "Market Cap (Cr)",
    "return_on_equity_pct": "ROE (%)",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)",
    "dividend_payout_ratio_pct": "Div Payout (%)"
})

st.subheader(f"{selected_pattern} — {len(sub_df)} Companies")
st.dataframe(sub_df, use_container_width=True, hide_index=True)