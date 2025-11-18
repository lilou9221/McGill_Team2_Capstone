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
# Check for required dependencies and install if missing (for Streamlit Cloud)
def ensure_dependency(package_name, import_name=None):
    """Ensure a Python package is installed, try to install if missing."""
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
# Check for PyYAML
if not ensure_dependency("PyYAML", "yaml"):
    st.error(
        "**Missing Dependency: PyYAML**\n\n"
        "PyYAML could not be installed automatically. Please ensure it's in requirements.txt:\n\n"
        "```txt\nPyYAML>=6.0\n```\n\n"
        "For Streamlit Cloud, restart your deployment after updating requirements.txt."
    )
    st.stop()
import yaml
# Project setup
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
# Load config
@st.cache_data
def load_config():
    cfg_path = PROJECT_ROOT / "configs" / "config.yaml"
    with open(cfg_path, encoding='utf-8') as f:
        return yaml.safe_load(f)
config = load_config()
# Page config
st.set_page_config(
    page_title="Biochar Suitability Mapper",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Enhanced Custom CSS - Inspired by Residual Carbon (Clean, Modern, Earthy Tones)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main > div {padding-top: 1.5rem;}
    body {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #1e293b;
    }
    .header-title {
        font-size: 3.2rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #10b981, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    .header-subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 2.5rem;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
        text-transform: none;
        letter-spacing: 0.025em;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #059669, #047857);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        transform: translateY(-1px);
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(16, 185, 129, 0.1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(135deg, #10b981, #059669);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    .metric-card h4 {
        margin: 0 0 0.5rem 0;
        color: #10b981;
        font-size: 0.95rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card p {
        font-size: 2.2rem;
        margin: 0;
        color: #1e293b;
        font-weight: 700;
        line-height: 1.1;
    }
    
    /* DataFrames and Tables */
    .stDataFrame, .stTable {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
    }
    .stSidebar .stMarkdown {
        color: #1e293b;
    }
    
    /* Code and Logs */
    .stCodeBlock, .stCode, code, pre {
        color: #1e293b !important;
        background-color: rgba(248, 250, 252, 0.8) !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        font-family: 'Inter', monospace !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Expander */
    .streamlit-expanderContent {
        color: #1e293b !important;
        background: rgba(255, 255, 255, 0.7);
        border-radius: 8px;
    }
    .stExpander {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.6);
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #1e40af);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2.5rem 0;
        color: #64748b;
        font-size: 0.95rem;
        font-weight: 400;
        border-top: 1px solid #e2e8f0;
        margin-top: 3rem;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 12px 12px 0 0;
    }
    .footer strong {
        color: #10b981;
        font-weight: 600;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #10b981, #059669);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #059669, #047857);
    }
    
    /* Subheaders */
    .stMarkdown h2 {
        color: #1e293b;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Info/Warning/Success Boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
        padding: 1rem 1.25rem;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)
# Header
st.markdown('<div class="header-title">Biochar Suitability Mapper</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Precision mapping for sustainable biochar application in Mato Grosso, Brazil</div>', unsafe_allow_html=True)
# Sidebar
with st.sidebar:
    st.markdown("### 🌍 Analysis Scope")
    use_coords = st.checkbox("Analyze radius around a point", value=False)
    lat = lon = radius = None
    if use_coords:
        col1, col2 = st.columns(2)
        lat = col1.number_input("Latitude", value=-13.0, step=0.1, format="%.4f")
        lon = col2.number_input("Longitude", value=-56.0, step=0.1, format="%.4f")
        radius = st.slider("Radius (km)", min_value=25, max_value=100, value=100, step=25)
        st.info(f"Analysis radius: **{radius} km**")
    else:
        st.info("Full **Mato Grosso state** analysis")
    h3_res = st.slider("H3 resolution", 5, 9, config["processing"].get("h3_resolution", 7))
    run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
# Run analysis
if run_btn:
    with st.spinner("Initializing..."):
        tmp_raw = Path(tempfile.mkdtemp(prefix="rc_raw_"))
        raw_dir = PROJECT_ROOT / config["data"]["raw"]
        raw_dir.mkdir(parents=True, exist_ok=True)
        # Check if GeoTIFFs are already cached
        if raw_dir.exists() and len(list(raw_dir.glob("*.tif"))) >= 5:
            st.info("Using cached GeoTIFFs")
            shutil.copytree(raw_dir, tmp_raw, dirs_exist_ok=True)
        else:
            st.warning("GeoTIFFs not found. Downloading from Google Drive...")
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaIoBaseDownload
                creds_info = json.loads(st.secrets["google_drive"]["credentials"])
                credentials = service_account.Credentials.from_service_account_info(
                    creds_info, scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                service = build('drive', 'v3', credentials=credentials)
                folder_id = config["drive"]["raw_data_folder_id"]
                results = service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false and mimeType!='application/vnd.google-apps.folder'",
                    fields="files(id, name)"
                ).execute()
                files = results.get('files', [])
                tif_files = [f for f in files if f['name'].endswith('.tif')]
                if not tif_files:
                    st.error("No .tif files found in Drive folder.")
                    st.stop()
                for file in tif_files:
                    filepath = raw_dir / file['name']
                    if not filepath.exists():
                        with st.spinner(f"Downloading {file['name']}..."):
                            request = service.files().get_media(fileId=file['id'])
                            fh = io.BytesIO()
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while not done:
                                status, done = downloader.next_chunk()
                            fh.seek(0)
                            with open(filepath, 'wb') as f:
                                f.write(fh.read())
                    else:
                        st.info(f"{file['name']} already downloaded")
                st.success("All GeoTIFFs downloaded!")
                shutil.copytree(raw_dir, tmp_raw, dirs_exist_ok=True)
            except Exception as e:
                st.error(f"Drive download failed: {e}")
                st.stop()
        # === RUN MAIN PIPELINE ===
        wrapper_script = PROJECT_ROOT / "run_analysis.py"
        cli = [
            sys.executable, str(wrapper_script),
            "--config", str(PROJECT_ROOT / "configs" / "config.yaml"),
            "--h3-resolution", str(h3_res),
        ]
        if lat and lon and radius:
            cli += ["--lat", str(lat), "--lon", str(lon), "--radius", str(radius)]
        status_container = st.empty()
        log_container = st.empty()
        with status_container.container():
            st.info("Starting analysis pipeline... This may take 2-5 minutes.")
        proc = subprocess.Popen(
            cli,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={
                **os.environ,
                "PYTHONPATH": str(PROJECT_ROOT),
                "PYTHONUNBUFFERED": "1"
            },
            universal_newlines=True
        )
        output_lines = []
        last_update = 0
        update_interval = 0.5
        start_time = time.time()
        while True:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.1)
                continue
            output_lines.append(line)
            current_time = time.time()
            if current_time - last_update > update_interval:
                elapsed = int(current_time - start_time)
                with status_container.container():
                    st.info(f"Running... ({elapsed}s elapsed)")
                recent_lines = output_lines[-10:] if len(output_lines) > 10 else output_lines
                with log_container.expander("View progress log", expanded=False):
                    st.code("".join(recent_lines))
                last_update = current_time
        remaining_output, _ = proc.communicate()
        if remaining_output:
            output_lines.append(remaining_output)
        returncode = proc.returncode
        full_output = "".join(output_lines)
        elapsed_total = int(time.time() - start_time)
        with status_container.container():
            if returncode == 0:
                st.success(f"Analysis completed successfully! ({elapsed_total}s)")
            else:
                st.error(f"Analysis failed after {elapsed_total}s")
        shutil.rmtree(tmp_raw, ignore_errors=True)
        if returncode != 0:
            st.error("Analysis failed")
            if "ModuleNotFoundError" in full_output and "yaml" in full_output.lower():
                st.error(
                    "**PyYAML Missing in Subprocess**\n\n"
                    "The analysis pipeline requires PyYAML. Please ensure `pyyaml>=6.0` is in requirements.txt "
                    "and restart your Streamlit Cloud deployment.\n\n"
                    "Current requirements.txt should include:\n"
                    "```txt\npyyaml>=6.0\n```"
                )
            with st.expander("View error log"):
                st.code(full_output)
            st.stop()
    # === DISPLAY RESULTS ===
    csv_path = PROJECT_ROOT / config["data"]["processed"] / "suitability_scores.csv"
    if not csv_path.exists():
        st.error("Results not generated.")
        st.stop()
    df = pd.read_csv(csv_path)
    st.success("Analysis complete!")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <h4>Hexagons</h4>
            <p>{len(df):,}</p>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        mean = df['suitability_score'].mean()
        st.markdown(f'''
        <div class="metric-card">
            <h4>Mean Score</h4>
            <p>{mean:.2f}/10</p>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        high = (df['suitability_score'] >= 8).sum()
        st.markdown(f'''
        <div class="metric-card">
            <h4>High Suitability</h4>
            <p>{high:,}</p>
        </div>
        ''', unsafe_allow_html=True)
    st.subheader("📊 Suitability Scores")
    st.dataframe(df.sort_values("suitability_score", ascending=False), use_container_width=True, hide_index=True)
    csv_data = df.to_csv(index=False).encode()
    st.download_button(
        "📥 Download CSV",
        csv_data,
        "biochar_suitability_scores.csv",
        "text/csv",
        use_container_width=True
    )
    html_path = PROJECT_ROOT / config["output"]["html"] / "suitability_map.html"
    if html_path.exists():
        st.subheader("🗺️ Interactive Suitability Map")
        with open(html_path, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=700, scrolling=True)
    else:
        st.warning("Map not generated.")
# Footer
st.markdown("""
<div class="footer">
    <strong>Residual Carbon</strong> • McGill University Capstone<br>
    Promoting biodiversity through science-driven biochar deployment
</div>
""", unsafe_allow_html=True)
