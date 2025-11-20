# src/analysis/biochar_recommender.py
import pandas as pd
import numpy as np
from pathlib import Path

EXCEL_PATH = Path(__file__).parent.parent.parent / "data" / "raw" / "Dataset_feedstock_ML.xlsx"

def load_biochar_db():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Biochar Properties ")
    
    # Parse pore size column
    def parse_pore(text):
        if pd.isna(text): return np.nan, np.nan
        text = str(text)
        sa = pv = np.nan
        for part in text.replace(";", " ").split():
            if any(x in part for x in ["m²/g", "m^2/g", "m2/g"]):
                try: sa = float(part.split()[0])
                except: pass
            if any(x in part for x in ["cm³/g", "cm^3/g"]):
                try: pv = float(part.split()[0])
                except: pass
        return sa, pv
    
    df["Surface_Area_m2g"], df["Pore_Volume_cm3g"] = zip(*df["pore size"].apply(parse_pore))
    
    # Clean numeric columns
    numeric_cols = ["Fixed carbon content", "Volatile matter", "Ash content", "pH", "C (%)", "Final Temperature"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Create beautiful name like "Brazil Nut Shell (850°C)"
    df["Temp"] = df["Final Temperature"].fillna(0).astype(int)
    df["Full_Name"] = df["Type"].fillna("Unknown") + " (" + df["Temp"].astype(str) + "°C)"
    df["Full_Name"] = df["Full_Name"].str.replace(" (0°C)", "").str.strip()
    
    return df

BIOCHAR_DB = load_biochar_db()
print(f"✓ Biochar database loaded: {len(BIOCHAR_DB)} entries")

def score_biochar(row, targets):
    score = 0.0
    weight = 100.0 / max(sum(1 for v in targets.values() if v is not None), 1)
    
    if targets.get("fc_min") is not None and pd.notna(row["Fixed carbon content"]) and row["Fixed carbon content"] >= targets["fc_min"]: score += weight
    if targets.get("fc_max") is not None and pd.notna(row["Fixed carbon content"]) and row["Fixed carbon content"] <= targets["fc_max"]: score += weight
    if targets.get("vm_min") is not None and pd.notna(row["Volatile matter"]) and row["Volatile matter"] >= targets["vm_min"]: score += weight
    if targets.get("vm_max") is not None and pd.notna(row["Volatile matter"]) and row["Volatile matter"] <= targets["vm_max"]: score += weight
    if targets.get("ash_min") is not None and pd.notna(row["Ash content"]) and row["Ash content"] >= targets["ash_min"]: score += weight
    if targets.get("ash_max") is not None and pd.notna(row["Ash content"]) and row["Ash content"] <= targets["ash_max"]: score += weight
    if targets.get("ph_min") is not None and pd.notna(row["pH"]) and row["pH"] >= targets["ph_min"]: score += weight
    if targets.get("ph_max") is not None and pd.notna(row["pH"]) and row["pH"] <= targets["ph_max"]: score += weight
    if targets.get("sa_min") is not None and pd.notna(row["Surface_Area_m2g"]) and row["Surface_Area_m2g"] >= targets["sa_min"]: score += weight
    
    return score

def recommend_biochar(hex_df: pd.DataFrame) -> pd.DataFrame:
    db = BIOCHAR_DB.copy()
    results = []
    
    for _, h in hex_df.iterrows():
        soc = h.get("mean_soc", 0) / 10.0      # g/kg → %
        moisture = h.get("mean_moisture", 0) * 100
        ph = h.get("mean_ph", 7.0)

        if soc > 5.0:
            name = "No biochar application recommended"
            reason = "SOC already high (>5%)"
        else:
            # Define target profile
            targets = {"fc_max": 50, "vm_min": 30, "ash_min": 40, "ph_min": 10} if moisture >= 80 else {"fc_min": 60, "fc_max": 85, "vm_max": 20, "ash_max": 20, "ph_min": 7, "ph_max": 9.5, "sa_min": 150}
            
            if ph < 6.0:
                targets.update({"ash_min": 25, "ph_min": 11, "sa_min": 200})
                reason = "Acidic soil"
            elif ph > 7.0:
                targets.update({"ash_max": 10, "ph_max": 6.0})
                reason = "Alkaline soil"
            else:
                reason = "Neutral pH"
                
            reason += " + " + ("High" if moisture >= 80 else "Low") + " moisture"
            
            db["score"] = db.apply(lambda r: score_biochar(r, targets), axis=1)
            best = db.loc[db["score"].idxmax()]
            name = best["Full_Name"]
        
        results.append({
            "Recommended_Feedstock": name,
            "Recommendation_Reason": reason
        })
    
    return pd.concat([hex_df, pd.DataFrame(results, index=hex_df.index)], axis=1)
