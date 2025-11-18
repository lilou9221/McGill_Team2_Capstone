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

# ============================================================
# DEPENDENCY CHECK
# ============================================================
def ensure_dependency(package_name, import_name=None):
    import_name = import_name or package_name
    try:
        __import__(import_name)
        return True
    except ImportError:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package_name, "--quiet"
            ])
            __import__(import_name)
            return True
        except Exception:
            return False

if not ensure_dependency("PyYAML", "yaml"):
    st.error("PyYAML missing. Add to requirements.txt:\nPyYAML>=6.0")
    st.stop()

import yaml

# ============================================================
# PROJECT SETUP
# ============================================================
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

@st.cache_data
def load_config():
    cfg = PROJECT_ROOT / "configs" / "config.yaml"
    with open(cfg, encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Biochar Suitability Mapper",
    page_icon="Leaf",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS — Dark green sidebar + Residual Carbon style
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    body, .stApp {font-family: 'Inter', sans-serif;}
    
    .header-title {
        font-size: 2.8rem;
        text-align: center;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #2d3a3a;
    }
    .header-subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }

    /* Dark Green Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0C2F29 !important;
        padding-top: 2rem !important;
    }
    section[data-testid="stSidebar"] * {color: white !important;}
    section[data-testid="stSidebar"] .stMarkdown h3 {font-size: 1.1rem; font-weight: 600;}

    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] [data-baseweb="input"] > div {
        background-color: #12473F !important;
        color: white !important;
        border: 1px solid #88BFB3 !important;
        border-radius: 8px !important;
    }

    /* Buttons — Green */
    .stButton > button,
    section[data-testid="stSidebar"] button {
        background-color: #234F38 !important;
        color: white !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .stButton > button:hover,
    section[data-testid="stSidebar"] button:hover {
        background-color: #193829 !important;
    }

    .stDownloadButton > button {
        background-color: #234F38 !important;
        color: white !important;
        border-radius: 999px !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button:hover {
        background-color: #193829 !important;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.3rem;
        border-radius: 12px;
        border-left: 4px solid #5D7B6A;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .metric-card h4 {margin: 0 0 0.5rem 0; color: #234F38; font-weight: 600;}
    .metric-card p {margin: 0; font-size: 2rem; font-weight: 700; color: #2d3a3a;}

    /* Code blocks */
    .stCodeBlock, code, pre {
        background-color: #f5f5f5 !important;
        color: #1a1a1a !important;
        border-radius: 6px !important;
        border: 1px solid #ddd !important;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #6c757d;
        font-size: 0.9rem;
        border-top: 1px solid #dee2e6;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="header-title">Biochar Suitability Mapper</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Precision mapping for sustainable biochar application in Mato Grosso, Brazil</div>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### Analysis Scope")

    use_coords = st.checkbox("Analyze area around a point", value=False)
    lat = lon = radius = None

    if use_coords:
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input("Latitude", value=-13.4500, step=0.1, format="%.6f")
        with col2:
            lon = st.number_input("Longitude", value=-56.0000, step=0.1, format="%.6f")
        radius = st.slider("Radius (km)", min_value=25, max_value=100, value=100, step=25)

    h3_res = st.slider(
        "H3 Resolution",
        min_value=5,
        max_value=9,
        value=config["processing"].get("h3_resolution", 7)
    )

    run_btn = st.button("Run Analysis", type="primary", use_container_width=True)

# ============================================================
# MAIN PIPELINE
# ============================================================
if run_btn:
    with st.spinner("Preparing data…"):
        tmp_raw = Path(tempfile.mkdtemp(prefix="rc_raw_"))
        raw_dir = PROJECT_ROOT / config["data"]["raw"]
        raw_dir.mkdir(parents=True, exist_ok=True)

        if len(list(raw_dir.glob("*.tif"))) >= 5:
            st.info("Using cached GeoTIFFs")
            shutil.copytree(raw_dir, tmp_raw, dirs_exist_ok=True)
        else:
            st.warning("Downloading GeoTIFFs from Google Drive…")
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaIoBaseDownload

                creds = json.loads(st.secrets["google_drive"]["credentials"])
                credentials = service_account.Credentials.from_service_account_info(
                    creds, scopes=["https://www.googleapis.com/auth/drive.readonly"]
                )
                service = build("drive", "v3", credentials=credentials)
                folder_id = config["drive"]["raw_data_folder_id"]

                results = service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="files(id, name)"
                ).execute()

                for file in results.get("files", []):
                    if not file["name"].endswith(".tif"):
                        continue
                    dst = raw_dir / file["name"]
                    if dst.exists():
                        continue
                    with st.spinner(f"Downloading {file['name']}…"):
                        request = service.files().get_media(fileId=file["id"])
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            _, done = downloader.next_chunk()
                        fh.seek(0)
                        dst.write_bytes(fh.read())

                shutil.copytree(raw_dir, tmp_raw, dirs_exist_ok=True)
                st.success("All GeoTIFFs ready")

            except Exception as e:
                st.error(f"Download failed: {e}")
                st.stop()

        # Run analysis
        cli = [
            sys.executable,
            str(PROJECT_ROOT / "run_analysis.py"),
            "--config", str(PROJECT_ROOT / "configs" / "config.yaml"),
            "--h3-resolution", str(h3_res)
        ]
        if use_coords and lat and lon and radius:
            cli += ["--lat", str(lat), "--lon", str(lon), "--radius", str(radius)]

        status = st.empty()
        log_expander = st.expander("Live log", expanded=False)

        process = subprocess.Popen(
            cli,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        logs = []
        start_time = time.time()
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                logs.append(line)
                status.info(f"Running… {int(time.time() - start_time)}s elapsed")
                log_expander.code("".join(logs[-15:]))

        if process.returncode != 0:
            st.error("Analysis failed")
            st.code("".join(logs))
            st.stop()

    # ============================================================
    # RESULTS
    # ============================================================
    csv_path = PROJECT_ROOT / config["data"]["processed"] / "suitability_scores.csv"
    if not csv_path.exists():
        st.error("Results file not found")
        st.stop()

    df = pd.read_csv(csv_path)
    st.success("Analysis completed successfully!")

    # Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Total Hexagons</h4>
            <p>{len(df):,}</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Mean Score</h4>
            <p>{df['suitability_score'].mean():.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>High Suitability (≥8)</h4>
            <p>{(df['suitability_score'] >= 8).sum():,}</p>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Suitability Scores")
    st.dataframe(
        df.sort_values("suitability_score", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        label="Download Results as CSV",
        data=df.to_csv(index=False).encode(),
        file_name="biochar_suitability_scores.csv",
        mime="text/csv",
        use_container_width=True
    )

    map_path = PROJECT_ROOT / config["output"]["html"] / "suitability_map.html"
    if map_path.exists():
        st.subheader("Interactive Suitability Map")
        with open(map_path, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=720, scrolling=True)
    else:
        st.warning("Map file not generated")

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
    <strong>Residual Carbon</strong> • McGill University<br>
    Data-driven biochar deployment for ecological impact.
</div>
""", unsafe_allow_html=True)
