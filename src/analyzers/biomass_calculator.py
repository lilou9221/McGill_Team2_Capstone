import pandas as pd
import yaml
from pathlib import Path

def load_crop_config():
    with open("configs/crop_config.yaml") as f:
        return yaml.safe_load(f)

def load_harvest_data():
    path = "data/raw/brazil_crop_harvest_area_2017-2024.xlsx"
    return pd.read_excel(path)

def get_latest_year_data(df: pd.DataFrame, crop_pt_name: str, state: str = None):
    # Filter exact Portuguese crop name
    mask_crop = df["Crop"] == crop_pt_name
    df_crop = df[mask_crop].copy()
    
    if state:
        df_crop = df_crop[df_crop["Municipality"].str.contains(f"({state})", case=False)]
    
    # Latest year available
    latest_year = df_crop["Year"].max()
    df_latest = df_crop[df_crop["Year"] == latest_year].copy()
    
    # Calculate production (tons) from area × average MT yield if missing
    # (some rows have area only → we’ll impute later if needed)
    return df_latest, latest_year

def calculate_biochar_potential(
    harvested_area_ha: float,
    yield_kg_ha: float,
    residue_ratio: float,
    pyrolysis_yield: float = 0.30
):
    grain_t = (yield_kg_ha * harvested_area_ha) / 1000
    residue_t = grain_t * residue_ratio
    biochar_t = residue_t * pyrolysis_yield
    return {
        "grain_t": round(grain_t, 2),
        "residue_t": round(residue_t, 2),
        "biochar_t": round(biochar_t, 2),
        "biochar_t_per_ha": round(biochar_t / harvested_area_ha, 3) if harvested_area_ha else 0
    }

def enhance_with_biomass(
    df: pd.DataFrame,
    crop_key: str,                     # 'soybean' | 'maize' | etc.
    farmer_yield_kg_ha: float = None   # optional override
):
    config = load_crop_config()
    crop = config["crops"][crop_key]
    ratio = crop["residue_ratio"]
    pyro = config["pyrolysis_yield"]
    
    # Use farmer input or fall back to Mato Grosso 2024 averages (hardcoded for reliability)
    default_yields = {
        "soybean": 3520,
        "maize": 6200,
        "sugarcane": 78500,
        "cotton": 1780
    }
    yield_used = farmer_yield_kg_ha or default_yields[crop_key]
    
    results = df["Harvested_area_ha"].apply(
        lambda area: calculate_biochar_potential(area, yield_used, ratio, pyro)
    )
    results_df = pd.json_normalize(results)
    
    enhanced = pd.concat([df.reset_index(drop=True), results_df], axis=1)
    enhanced["Yield_used_kg_ha"] = yield_used
    enhanced["Crop_Selected"] = crop["english"]
    
    # Sort by biggest biochar potential
    enhanced = enhanced.sort_values("biochar_t", ascending=False)
    
    return enhanced
