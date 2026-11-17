import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.dashboard.utils.db import get_companies, get_documents

st.set_page_config(page_title="Annual Reports | Nifty 100 Analytics", layout="wide")
st.title("📄 BSE Annual Reports Repository")

companies = get_companies()
options = [f"{r['company_id']} — {r['company_name']}" for _, r in companies.iterrows()]
selected = st.selectbox("Search & Select Company", options=options)
ticker = selected.split(" — ")[0].strip()

docs = get_documents(ticker=ticker).copy()

if docs.empty:
    st.info(f"No annual report records found for {ticker}.")
    st.stop()

docs = docs.sort_values("Year", ascending=False)

@st.cache_data(ttl=3600)
def check_pdf_url(url: str) -> bool:
    if not url or not str(url).startswith("http"):
        return False
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.head(url, headers=headers, timeout=4, allow_redirects=True)
        if resp.status_code == 404:
            return False
        if resp.status_code >= 400:
            # Some servers block HEAD; fallback to lightweight GET stream check
            resp_get = requests.get(url, headers=headers, timeout=4, stream=True)
            return resp_get.status_code == 200
        return resp.status_code == 200
    except Exception:
        return False

st.subheader(f"Available Annual Reports for {ticker}")

for _, row in docs.iterrows():
    yr = row["Year"]
    url = str(row["Annual_Report"]).strip()
    is_valid = check_pdf_url(url)

    c1, c2 = st.columns([1, 4])
    c1.markdown(f"**FY {yr}**")
    if is_valid:
        c2.markdown(f"📄 [Open / Download FY {yr} Annual Report (BSE PDF)]({url})")
    else:
        c2.markdown(
            '<span style="background-color:#d9534f;color:white;padding:3px 10px;border-radius:6px;font-size:0.85em;font-weight:600;">Report unavailable</span>',
            unsafe_allow_html=True
        )