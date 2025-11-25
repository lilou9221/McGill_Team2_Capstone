"""
Biomass Calculator - Data Loading Module

Loads crop residue ratios and harvest data for biochar yield calculations.
Data is cached for 1 hour to avoid repeated file reads.
"""

import pandas as pd
import streamlit as st
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()


@st.cache_data(ttl=3600)
def load_residue_ratios() -> pd.DataFrame:
    """
    Load crop residue ratio data from CSV.
    
    Returns:
        pd.DataFrame: Residue ratios by crop type (URR values).
    """
    return pd.read_csv(PROJECT_ROOT / "data" / "residue_ratios.csv")


@st.cache_data(ttl=3600)
def load_harvest_data() -> pd.DataFrame:
    """
    Load Brazil crop harvest data (2017-2024). Cached for 1 hour.
    
    Returns:
        pd.DataFrame: Harvest area and production by municipality/year.
    """
    return pd.read_csv(PROJECT_ROOT / "data" / "brazil_crop_harvest_area_2017-2024.csv")
