# streamlit_app.py
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import subprocess
import shutil
import tempfile
import os
import json
import io
import time

# === Dependency check ===
def ensure_dependency(package_name, import_name=None):
    import_name = import_name or package_name
    try:
        __import__(import_name)
        return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--quiet"])
            __import__(import_name)
            return True
        except Exception:
            return False

if not ensure_dependency("PyYAML", "yaml"):
    st.error("Missing PyYAML — add `PyYAML>=6.0` to requirements.txt and redeploy.")
    st.stop()
import yaml

# === Project setup ===
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

@st.cache_data
def load_config():
    cfg_path = PROJECT_ROOT / "configs" / "config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
config = load_config()

st.set_page_config(
    page_title="Biochar Suitability Mapper",
    page_icon="leaf",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === BULLETPROOF CSS — 100% readable dark text everywhere ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
    .stApp {background-color: #ffffff !important;}

    :root {
        --rc-green: #2d6b5e;
        --rc-green-dark: #1f4e45;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border: #e2e8f0;
    }

    /* Force ALL text to be dark */
    .stMarkdown, .stText, p, div, span, label, h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {color: var(--text-primary) !important;}

    /* Header */
    .header-title {
        font-size: 3rem; font-weight: 700; text-align: center;
        color: var(--text-primary); margin-bottom: 0.5rem; letter-spacing: -0.8px;
    }
    .header-subtitle {
        text-align: center; color: var(--text-secondary); font-size: 1.15rem;
        max-width: 820px; margin: 0 auto 3rem auto; line-height: 1.6;
    }

    /* Buttons — forced dark text + green bg */
    .stButton > button {
        background-color: var(--rc-green) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        background-color: var(--rc-green-dark) !important;
        box-shadow: 0 8px 25px rgba(45,107,94,0.25) !important;
    }

    /* Fix Streamlit alerts (success/info/warning/error) — no white text! */
    .stAlert {
        color: var(--text-primary) !important;
        background-color: #f8fafc !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    .stAlert > div {color: var(--text-primary) !important;}

    /* Metric cards */
    .metric-card {
        background: white; padding: 1.75rem; border-radius: 12px;
        border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: all 0.25s ease;
    }
    .metric-card:hover {transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.1);}
    .metric-card h4 {
        color: var(--rc-green); font-size: 0.9rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.8px; margin: 0 0 0.5rem 0;
    }
    .metric-card p {
        font-size: 2.4rem; font-weight: 700; color: var(--text-primary); margin: 0;
    }

    /* Tables & code */
    .stDataFrame {border-radius: 12px; border: 1px solid var(--border);}
    code, pre, .stCodeBlock {background: #f8fafc !important; color: var(--text-primary) !important;}

    /* Download button */
    .stDownloadButton > button {
        background-color: var(--rc-green) !important;
        color: white !important;
    }
    .stDownloadButton > button:hover {
        background-color: var(--rc-green-dark) !important;
    }

    /* Footer */
    .footer {
        text-align: center; padding: 3rem 0 2rem; color: var(--text-secondary);
        font-size: 0.95rem; border-top: 1px solid var(--border); margin-top: 4rem;
    }
    .footer strong {color: var(--rc-green);}
</style>
""", unsafe_allow_html=True)

# === Header ===
st.markdown('<div class="header-title">Biochar Suitability Mapper</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Precision mapping for sustainable biochar application in Mato Grosso, Brazil</div>', unsafe_allow_html=True)

# === Sidebar ===
with st.sidebar:
    st.markdown("### Analysis Scope")
    use_coords = st.checkbox("Analyze radius around a point", value=False)
    lat = lon = radius = None
    if use_coords:
        col1, col2 = st.columns(2)
        lat = col1.number_input("Latitude", value=-13.0, step=0.1, format="%.4f")
        lon = col2.number_input("Longitude", value=-56.0, step=0.1, format="%.4f")
        radius = st.slider("Radius (km)", 25, 100, 100, 25)
        st.info(f"Analysis radius: {radius} km")
    else:
        st.info("Full Mato Grosso state analysis")
    
    h3_res = st.slider("H3 resolution", 5, 9, config["processing"].get("h3_resolution", 7))
    run_btn = st.button("Run Analysis", type="primary", use_container_width=True)

# === Analysis (unchanged logic) ===
if run_btn:
    # ... [your entire analysis block from previous version] ...
    # Only change: all st.success/info/warning now have dark text guaranteed
    # (code omitted here for brevity — copy-paste your working block)

    # Example of safe status messages:
    with st.spinner("Initializing..."):
        # your full code here
        pass

    st.success("Analysis complete")  # ← now 100% visible

    # Results display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><h4>Hexagons</h4><p>{len(df):,}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h4>Mean Score</h4><p>{df["suitability_score"].mean():.2f}/10</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h4>High Suitability (≥8)</h4><p>{(df["suitability_score"] >= 8).sum():,}</p></div>', unsafe_allow_html=True)

    st.subheader("Suitability Scores")
    st.dataframe(df.sort_values("suitability_score", ascending=False), use_container_width=True, hide_index=True)

    st.download_button(
        "Download Results as CSV",
        df.to_csv(index=False).encode(),
        "biochar_suitability_scores.csv",
        "text/csv",
        use_container_width=True
    )

    html_path = PROJECT_ROOT / config["output"]["html"] / "suitability_map.html"
    if html_path.exists():
        st.subheader("Interactive Suitability Map")
        with open(html_path, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=720, scrolling=True)

# === Footer ===
st.markdown("""
<div class="footer">
    <strong>Residual Carbon</strong> • McGill University Capstone<br>
    Promoting biodiversity through science-driven biochar deployment
</div>
""", unsafe_allow_html=True)
