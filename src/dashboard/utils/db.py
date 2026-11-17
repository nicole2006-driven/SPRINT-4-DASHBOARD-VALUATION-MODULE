import re
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"

def _load_excel(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    df = pd.read_excel(path)
    first_col = str(df.columns[0])
    if "Nifty 100" in first_col or first_col.startswith("Unnamed"):
        df = pd.read_excel(path, skiprows=1)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def _extract_year_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.extract(r"(\d{4})")[0], errors="coerce")

def _extract_pct(series: pd.Series, target_horizon: str = "5 Years") -> pd.Series:
    """Extracts the percentage for '5 Years' (or fallback first available %) across multi-row analysis records."""
    def parse_val(val):
        if pd.isna(val):
            return np.nan
        s = str(val)
        if target_horizon in s:
            m = re.search(r"([-\d.]+)%", s)
            return float(m.group(1)) if m else np.nan
        return np.nan
    return series.apply(parse_val)

@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    df = _load_excel("companies.xlsx")
    if "id" in df.columns and "company_id" not in df.columns:
        df["company_id"] = df["id"].astype(str).str.strip()
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker: str = None, year: int = None) -> pd.DataFrame:
    df = _load_excel("financial_ratios.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    df["year_int"] = _extract_year_int(df["year"])
    if ticker is not None:
        df = df[df["company_id"] == ticker]
    if year is not None:
        df = df[df["year_int"] == int(year)]
    return df

@st.cache_data(ttl=600)
def get_pl(ticker: str = None) -> pd.DataFrame:
    df = _load_excel("profitandloss.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df[df["company_id"] == ticker] if ticker is not None else df

@st.cache_data(ttl=600)
def get_bs(ticker: str = None) -> pd.DataFrame:
    df = _load_excel("balancesheet.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df[df["company_id"] == ticker] if ticker is not None else df

@st.cache_data(ttl=600)
def get_cf(ticker: str = None) -> pd.DataFrame:
    df = _load_excel("cashflow.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df[df["company_id"] == ticker] if ticker is not None else df

@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    df = _load_excel("sectors.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df

@st.cache_data(ttl=600)
def get_peers(group_name: str = None) -> pd.DataFrame:
    df = _load_excel("peer_groups.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df[df["peer_group_name"] == group_name] if group_name is not None else df

@st.cache_data(ttl=600)
def get_market_cap(ticker: str = None, year: int = None) -> pd.DataFrame:
    df = _load_excel("market_cap.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    df["year_int"] = _extract_year_int(df["year"])
    if ticker is not None:
        df = df[df["company_id"] == ticker]
    if year is not None:
        df = df[df["year_int"] == int(year)]
    return df

@st.cache_data(ttl=600)
def get_analysis() -> pd.DataFrame:
    df = _load_excel("analysis.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    df["sales_cagr_5yr"] = _extract_pct(df["compounded_sales_growth"], "5 Years")
    df["pat_cagr_5yr"] = _extract_pct(df["compounded_profit_growth"], "5 Years")
    df["roe_5yr"] = _extract_pct(df["roe"], "5 Years")
    # Collapse multi-horizon rows into 1 clean row per company_id
    df = df.groupby("company_id", as_index=False).agg({
        "sales_cagr_5yr": "first",
        "pat_cagr_5yr": "first",
        "roe_5yr": "first"
    })
    return df

@st.cache_data(ttl=600)
def get_prosandcons(ticker: str = None) -> pd.DataFrame:
    df = _load_excel("prosandcons.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df[df["company_id"] == ticker] if ticker is not None else df

@st.cache_data(ttl=600)
def get_documents(ticker: str = None) -> pd.DataFrame:
    df = _load_excel("documents.xlsx")
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df[df["company_id"] == ticker] if ticker is not None else df

@st.cache_data(ttl=600)
def get_valuation(ticker: str = None) -> pd.DataFrame:
    val_path = OUTPUT_DIR / "valuation_summary.xlsx"
    if not val_path.exists():
        return pd.DataFrame()
    df = pd.read_excel(val_path)
    df["company_id"] = df["company_id"].astype(str).str.strip()
    return df[df["company_id"] == ticker] if ticker is not None else df