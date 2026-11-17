# Nifty 100 Analytics & Valuation Platform

An 8-screen interactive equity research and valuation dashboard built with **Streamlit**, **Plotly**, and **Pandas**, covering **92 Nifty 100 companies** across broad sectors and peer groups.

---

## Project Structure

```text
Nifty100_Analytics/
├── data/                        # Production Excel datasets (12 .xlsx files)
├── output/                      # Generated valuation reports
│   ├── valuation_summary.xlsx   # 92 companies with multiples, FCF yield & flags
│   └── valuation_flags.csv      # Caution & Discount flagged companies
├── pages/                       # 8 Streamlit analytical screens
│   ├── 01_home.py               # Market overview KPIs, sector donut & Top-5 quality
│   ├── 02_profile.py            # Company 360° profile, 10Y charts & Pros/Cons
│   ├── 03_screener.py           # 10-slider screener, 6 presets & CSV download
│   ├── 04_peers.py              # 11 peer groups, Scatterpolar radar & KPI table
│   ├── 05_trends.py             # Multi-metric 10-year trajectories with YoY %
│   ├── 06_sectors.py            # Sector bubble chart & cross-sector median KPIs
│   ├── 07_capital.py            # 8-pattern Capital Allocation treemap
│   └── 08_reports.py            # BSE Annual Reports repository & 404 link check
├── src/
│   ├── analytics/
│   │   └── valuation.py         # FCF yield & sector-relative P/E valuation engine
│   └── dashboard/
│       ├── app.py               # Main Streamlit entry point & navigation
│       └── utils/
│           └── db.py            # Cached (@st.cache_data(ttl=600)) Excel data layer
├── requirements.txt
└── README.md