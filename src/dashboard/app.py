import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

pages = [
    st.Page(str(ROOT_DIR / "pages" / "01_home.py"), title="01 Home Overview", icon="🏠", default=True),
    st.Page(str(ROOT_DIR / "pages" / "02_profile.py"), title="02 Company Profile", icon="🏢"),
    st.Page(str(ROOT_DIR / "pages" / "03_screener.py"), title="03 Stock Screener", icon="🔎"),
    st.Page(str(ROOT_DIR / "pages" / "04_peers.py"), title="04 Peer Comparison", icon="⚖️"),
    st.Page(str(ROOT_DIR / "pages" / "05_trends.py"), title="05 Trend Analysis", icon="📈"),
    st.Page(str(ROOT_DIR / "pages" / "06_sectors.py"), title="06 Sector Analysis", icon="🏭"),
    st.Page(str(ROOT_DIR / "pages" / "07_capital.py"), title="07 Capital Allocation", icon="🧭"),
    st.Page(str(ROOT_DIR / "pages" / "08_reports.py"), title="08 Annual Reports", icon="📄"),
]

pg = st.navigation(pages)
pg.run()