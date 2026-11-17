import pandas as pd
import numpy as np
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_clean(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    df = pd.read_excel(path)
    if "Nifty 100" in str(df.columns[0]) or str(df.columns[0]).startswith("Unnamed"):
        df = pd.read_excel(path, skiprows=1)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def generate_valuation():
    companies = load_clean("companies.xlsx")
    companies["company_id"] = companies["id"].astype(str).str.strip()

    sectors = load_clean("sectors.xlsx")
    sectors["company_id"] = sectors["company_id"].astype(str).str.strip()

    mcap = load_clean("market_cap.xlsx")
    mcap["company_id"] = mcap["company_id"].astype(str).str.strip()

    ratios = load_clean("financial_ratios.xlsx")
    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()

    # Latest year per company in market_cap & ratios
    latest_mcap = mcap.sort_values("year").groupby("company_id", as_index=False).last()
    latest_ratios = ratios.sort_values("year").groupby("company_id", as_index=False).last()

    # 5-year median P/E per company
    mcap_sorted = mcap.sort_values(["company_id", "year"])
    pe_5yr = (
        mcap_sorted.groupby("company_id")["pe_ratio"]
        .apply(lambda s: s.dropna().tail(5).median())
        .reset_index()
        .rename(columns={"pe_ratio": "5yr_median_PE"})
    )

    # Base table with all 92 companies
    df = companies[["company_id", "company_name"]].merge(
        sectors[["company_id", "broad_sector"]].rename(columns={"broad_sector": "sector"}),
        on="company_id",
        how="left"
    )
    df = df.merge(
        latest_mcap[["company_id", "market_cap_crore", "pe_ratio", "pb_ratio", "ev_ebitda"]],
        on="company_id",
        how="left"
    )
    df = df.merge(
        latest_ratios[["company_id", "free_cash_flow_cr"]],
        on="company_id",
        how="left"
    )
    df = df.merge(pe_5yr, on="company_id", how="left")

    # Compute FCF Yield (%)
    df["FCF_yield_pct"] = np.where(
        (df["market_cap_crore"].notna()) & (df["market_cap_crore"] > 0),
        (df["free_cash_flow_cr"] / df["market_cap_crore"]) * 100.0,
        np.nan
    )

    # Sector median P/E in latest year
    sector_med = df.groupby("sector")["pe_ratio"].transform("median")

    df["PE_vs_sector_median_pct"] = np.where(
        (sector_med.notna()) & (sector_med != 0) & (df["pe_ratio"].notna()),
        ((df["pe_ratio"] - sector_med) / sector_med) * 100.0,
        np.nan
    )

    def assign_flag(row, sec_pe):
        pe = row["pe_ratio"]
        if pd.isna(pe) or pd.isna(sec_pe) or sec_pe <= 0:
            return "Fair"
        if pe > sec_pe * 1.5:
            return "Caution"
        if pe < sec_pe * 0.7:
            return "Discount"
        return "Fair"

    df["flag"] = [assign_flag(row, sec_pe) for (_, row), sec_pe in zip(df.iterrows(), sector_med)]

    # Rename & select exact required columns
    out = df.rename(columns={
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "ev_ebitda": "EV/EBITDA"
    })[[
        "company_id", "company_name", "sector", "P/E", "P/B",
        "EV/EBITDA", "FCF_yield_pct", "5yr_median_PE",
        "PE_vs_sector_median_pct", "flag"
    ]].copy()

    # Round numeric columns cleanly
    num_cols = ["P/E", "P/B", "EV/EBITDA", "FCF_yield_pct", "5yr_median_PE", "PE_vs_sector_median_pct"]
    out[num_cols] = out[num_cols].round(2)

    summary_path = OUTPUT_DIR / "valuation_summary.xlsx"
    flags_path = OUTPUT_DIR / "valuation_flags.csv"

    out.to_excel(summary_path, index=False)
    out[out["flag"].isin(["Caution", "Discount"])].to_csv(flags_path, index=False)
    print(f"Saved {len(out)} rows to {summary_path}")
    print(f"Saved {len(out[out['flag'].isin(['Caution', 'Discount'])])} flagged rows to {flags_path}")

if __name__ == "__main__":
    generate_valuation()