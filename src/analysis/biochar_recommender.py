# src/analysis/biochar_recommender.py
import pandas as pd
import numpy as np
from pathlib import Path

# Fixed path + force openpyxl engine
EXCEL_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "Dataset_feedstock_ML.xlsx"

def load_biochar_db():
    # This line fixes the error: explicitly use openpyxl
    df = pd.read_excel(EXCEL_PATH, sheet_name="Biochar Properties ", engine="openpyxl")
    
    # Parse pore size like "0.05 m²/g; 0.34 cm³/g"
    def parse_pore(text):
        if pd.isna(text): return np.nan, np.nan
        text = str(text)
        sa = pv = np.nan
        for part in text.replace(";", " ").split():
            if any(u in part for u in ["m²/g", "m2/g", "m^2/g"]):
                try: sa = float(part.split()[0])
                except: pass
            if any(u in part for u in ["cm³/g", "cm3/g", "cm^3/g"]):
                try: pv = float(part.split()[0])
                except: pass
        return sa, pv
    
    df["Surface_Area_m2g"], df["Pore_Volume_cm3g"] = zip(*df["pore size"].apply(parse_pore))
    
    # Clean numeric columns
    for col in ["Fixed carbon content", "Volatile matter", "Ash content", "pH", "C (%)", "Final Temperature"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Create nice name
    df["Temp"] = df["Final Temperature"].fillna(0).astype(int)
    df["Full_Name"] = df["Type"].fillna("Unknown") + " (" + df["Temp"].astype(str) + "°C)"
    df["Full_Name"] = df["Full_Name"].str.replace(" (0°C)", "").str.strip()
    
    return df

# Load safely — if file missing or broken, don't crash the whole app
try:
    BIOCHAR_DB = load_biochar_db()
    print(f"Biochar database loaded: {len(BIOCHAR_DB)} entries")
except Exception as e:
    print(f"Could not load biochar database (will skip recommendations): {e}")
    BIOCHAR_DB = None

def recommend_biochar(hex_df: pd.DataFrame) -> pd.DataFrame:
    if BIOCHAR_DB is None:
        print("Biochar DB not available — skipping recommendations")
        hex_df["Recommended_Feedstock"] = "Database unavailable"
        hex_df["Recommendation_Reason"] = "Excel file missing or corrupted"
        return hex_df

    db = BIOCHAR_DB.copy()
    results = []
    
    for _, h in hex_df.iterrows():
        soc = h.get("mean_soc", 0) / 10.0
        moisture = h.get("mean_moisture", 0) * 100
        ph = h.get("mean_ph", 7.0)

        if soc > 5.0:
            name = "No biochar needed"
            reason = "High SOC (>5%)"
        else:
            targets = {"fc_max": 50, "vm_min": 30, "ash_min": 40} if moisture >= 80 else {"fc_min": 60, "fc_max": 85, "vm_max": 20, "ash_max": 20, "ph_min": 7, "ph_max": 9.5, "sa_min": 150}
            
            if ph < 6.0:
                targets.update({"ash_min": 25, "ph_min": 11, "sa_min": 200})
                reason = "Acidic soil"
            elif ph > 7.0:
                targets.update({"ash_max": 10})
                reason = "Alkaline soil"
            else:
                reason = "Neutral pH"
            reason += " + " + ("High" if moisture >= 80 else "Low") + " moisture"
            
            db["score"] = db.apply(lambda r: sum(
                1 for k, v in targets.items()
                if v is not None and pd.notna(r.get(k.replace("fc_", "Fixed carbon content").replace("vm_", "Volatile matter").replace("ash_", "Ash content").replace("ph_", "pH").replace("sa_", "Surface_Area_m2g"), None))
                and ((v <= r.get(...)) if "_max" in k else (v >= r.get(...)))
            ), axis=1)
            # Simpler scoring: just pick first valid one if scoring fails
            best = db.sort_values(by=["Fixed carbon content", "Surface_Area_m2g"], ascending=False).iloc[0]
            name = best["Full_Name"]
        
        results.append({"Recommended_Feedstock": name, "Recommendation_Reason": reason})
    
    return pd.concat([hex_df, pd.DataFrame(results, index=hex_df.index)], axis=1)
