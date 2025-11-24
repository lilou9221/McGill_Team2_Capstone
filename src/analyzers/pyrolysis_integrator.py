# src/analyzers/pyrolysis_integrator.py
"""
Pyrolysis Data Integrator - Rule-Based Data Processing

Handles data loading, cleaning, type conversion, property extraction, and hierarchical lookup.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Dataset paths
PRIMARY_DATASET_PATH = Path(__file__).parent.parent.parent / "data" / "pyrolysis" / "pyrolysis_data.csv"
FALLBACK_DATASET_PATH = Path(__file__).parent.parent.parent / "data" / "pyrolysis" / "pyrolysis_data_fallback.csv"

# Numeric columns that need type conversion
NUMERIC_COLUMNS = [
    'Cellulose', 'Hemicellulose', 'Lignin', 'Ash content', 'Moisture content',
    'O (%)', 'C (%)', 'Fixed carbon content', 'Volatile matter',
    'Final Temperature', 'Heating Rate', 'Residence Time"" (min)',
    'Biochar Yield (%)', 'H/C ratio', 'O/C ratio', 'pH', 'pore size'
]

# Property columns of interest
PROPERTY_COLUMNS = {
    'ph': 'pH',
    'carbon_content': 'C (%)',
    'biochar_yield': 'Biochar Yield (%)',
    'oc_ratio': 'O/C ratio',
    'hc_ratio': 'H/C ratio'
}

# Challenge columns
CHALLENGE_COLUMNS = [
    'Challenge_High_Temperature', 'Challenge_High_pH', 'Challenge_Low_Moisture',
    'Challenge_Low_OC', 'Challenge_Low_pH'
]

# Similar feedstock grouping rules (order matters: more specific first)
SIMILAR_FEEDSTOCK_GROUPS = {
    'husk_types': {
        'feedstocks': ['Rice Husk'],
        'keywords': ['rice', 'arroz'],
        'residue_keywords': ['husk', 'casca']
    },
    'coffee_related': {
        'feedstocks': ['Coffee Silverskin', 'Spent Coffee Ground'],
        'keywords': ['coffee', 'café', 'cafe'],
        'residue_keywords': ['silverskin', 'ground', 'pulp']
    },
    'corn_related': {
        'feedstocks': ['Corn Straw', 'Corn cob'],
        'keywords': ['corn', 'milho', 'maize'],
        'residue_keywords': ['straw', 'stover', 'cob', 'stalk']
    },
    'legume_straws': {
        'feedstocks': ['Soybean Straw'],
        'keywords': ['soybean', 'soja', 'bean', 'pea', 'lentil', 'chickpea', 'legume'],
        'residue_keywords': ['straw', 'residue']
    },
    'grain_straws': {
        'feedstocks': ['Corn Straw', 'Soybean Straw'],
        'keywords': ['wheat', 'sorghum', 'oats', 'barley', 'rye', 'millet', 'grain', 'cereal', 'trigo'],
        'residue_keywords': ['straw', 'stover', 'residue']
    }
}


def load_pyrolysis_datasets() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Load primary and fallback pyrolysis datasets."""
    primary_df = None
    fallback_df = None
    
    if PRIMARY_DATASET_PATH.exists():
        try:
            primary_df = pd.read_csv(PRIMARY_DATASET_PATH)
            print(f"  Loaded primary pyrolysis data: {len(primary_df)} rows")
        except Exception as e:
            print(f"  Warning: Could not load primary dataset: {e}")
    else:
        print(f"  Warning: Primary dataset not found at {PRIMARY_DATASET_PATH}")
    
    if FALLBACK_DATASET_PATH.exists():
        try:
            fallback_df = pd.read_csv(FALLBACK_DATASET_PATH)
            print(f"  Loaded fallback pyrolysis data: {len(fallback_df)} rows")
        except Exception as e:
            print(f"  Warning: Could not load fallback dataset: {e}")
    else:
        print(f"  Warning: Fallback dataset not found at {FALLBACK_DATASET_PATH}")
    
    return primary_df, fallback_df


def clean_and_convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and convert string columns to numeric types. Handles ranges, empty strings, and missing values."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.replace('"', '')
    
    def parse_value(val):
        if pd.isna(val) or val == '':
            return np.nan
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        if '-' in val_str and not val_str.startswith('-'):
            parts = val_str.split('-')
            try:
                return (float(parts[0]) + float(parts[1])) / 2.0
            except (ValueError, IndexError):
                return np.nan
        try:
            return float(val_str)
        except (ValueError, TypeError):
            return np.nan
    
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(['', ' ', 'nan', 'None', 'null'], np.nan)
            df[col] = df[col].apply(parse_value)
    
    return df


def _process_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Process a single dataset: extract properties, ranges, and challenges."""
    result = {
        'properties': {},
        'ranges': {},
        'challenges': {}
    }
    
    # Extract properties (overall stats)
    for prop_key, col_name in PROPERTY_COLUMNS.items():
        if col_name in df.columns:
            values = df[col_name].dropna()
            result['properties'][prop_key] = {
                'values': values.tolist() if len(values) > 0 else [],
                'mean': float(values.mean()) if len(values) > 0 else np.nan,
                'min': float(values.min()) if len(values) > 0 else np.nan,
                'max': float(values.max()) if len(values) > 0 else np.nan,
                'count': len(values),
                'column': col_name
            }
        else:
            result['properties'][prop_key] = {
                'values': [], 'mean': np.nan, 'min': np.nan, 'max': np.nan, 'count': 0, 'column': col_name
            }
    
    # Extract property ranges per feedstock
    if 'Type' in df.columns:
        for feedstock in df['Type'].unique():
            if pd.isna(feedstock):
                continue
            feedstock_data = df[df['Type'] == feedstock]
            feedstock_ranges = {}
            for prop_key, col_name in PROPERTY_COLUMNS.items():
                if col_name in feedstock_data.columns:
                    values = feedstock_data[col_name].dropna()
                    feedstock_ranges[prop_key] = {
                        'min': float(values.min()) if len(values) > 0 else np.nan,
                        'max': float(values.max()) if len(values) > 0 else np.nan,
                        'mean': float(values.mean()) if len(values) > 0 else np.nan,
                        'count': len(values)
                    }
                else:
                    feedstock_ranges[prop_key] = {'min': np.nan, 'max': np.nan, 'mean': np.nan, 'count': 0}
            result['ranges'][str(feedstock)] = feedstock_ranges
    
    # Extract challenge information
    if 'Type' in df.columns and 'Soil Challenges to amend' in df.columns:
        challenge_col = 'Soil Challenges to amend'
        for feedstock in df['Type'].unique():
            if pd.isna(feedstock):
                continue
            feedstock_data = df[df['Type'] == feedstock]
            challenges = []
            
            # From "Soil Challenges to amend" column
            challenge_values = feedstock_data[challenge_col].dropna().unique()
            for val in challenge_values:
                if pd.notna(val) and val != '':
                    if ';' in str(val):
                        challenges.extend([c.strip() for c in str(val).split(';')])
                    else:
                        challenges.append(str(val).strip())
            
            # From challenge boolean columns
            for challenge_col_name in CHALLENGE_COLUMNS:
                if challenge_col_name in feedstock_data.columns and feedstock_data[challenge_col_name].any():
                    challenge_name = challenge_col_name.replace('Challenge_', '').replace('_', ' ')
                    if challenge_name not in challenges:
                        challenges.append(challenge_name)
            
            result['challenges'][str(feedstock)] = list(set(challenges))
    
    return result


def get_feedstock_properties(
    feedstock_name: str,
    primary_df: Optional[pd.DataFrame],
    fallback_df: Optional[pd.DataFrame],
    temperature: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """Get properties for a specific feedstock using hierarchical lookup (primary → fallback)."""
    def _find_in_dataset(df, name):
        if df is None or 'Type' not in df.columns:
            return None
        feedstock_data = df[df['Type'].str.strip().str.lower() == name.lower().strip()]
        if len(feedstock_data) == 0:
            return None
        
        # Filter by temperature if specified
        if temperature is not None and 'Final Temperature' in feedstock_data.columns:
            temp_col = feedstock_data['Final Temperature']
            if temp_col.notna().any():
                temp_diff = (temp_col - temperature).abs()
                feedstock_data = feedstock_data.loc[[temp_diff.idxmin()]]
        
        return feedstock_data.iloc[0]
    
    row = _find_in_dataset(primary_df, feedstock_name) or _find_in_dataset(fallback_df, feedstock_name)
    if row is not None:
        source = 'primary' if primary_df is not None and feedstock_name.lower() in primary_df['Type'].str.lower().values else 'fallback'
        return _extract_feedstock_dict(row, source)
    return None


def find_similar_feedstock(crop_name: str, residue_type: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """Find similar feedstock for a crop/residue using keyword matching."""
    if not crop_name:
        return None
    
    crop_lower = crop_name.lower().strip()
    residue_lower = residue_type.lower().strip() if residue_type else ""
    
    for group_name, group_info in SIMILAR_FEEDSTOCK_GROUPS.items():
        # Check crop name match
        crop_match = any(keyword == crop_lower or keyword in crop_lower.split() for keyword in group_info['keywords'])
        
        # Check residue match
        residue_match = any(keyword in residue_lower for keyword in group_info['residue_keywords']) if residue_type else False
        
        if crop_match or (residue_match and group_name in ['husk_types', 'coffee_related']):
            if group_info['feedstocks']:
                return (group_info['feedstocks'][0], group_name)
    
    return None


def get_feedstock_for_crop(
    crop_name: str,
    residue_type: Optional[str] = None,
    primary_df: Optional[pd.DataFrame] = None,
    fallback_df: Optional[pd.DataFrame] = None
) -> Optional[Dict[str, Any]]:
    """Get feedstock properties for a crop/residue: exact match → similar feedstock → None."""
    # Try exact match
    exact_name = f"{crop_name} {residue_type}" if residue_type else crop_name
    
    for df, source in [(primary_df, 'primary'), (fallback_df, 'fallback')]:
        if df is not None and 'Type' in df.columns:
            exact_match = df[df['Type'].str.strip().str.lower() == exact_name.lower().strip()]
            if len(exact_match) > 0:
                result = _extract_feedstock_dict(exact_match.iloc[0], source)
                result['match_type'] = 'exact'
                return result
    
    # Try similar feedstock grouping
    similar_match = find_similar_feedstock(crop_name, residue_type)
    if similar_match:
        feedstock_name, group_name = similar_match
        feedstock_props = get_feedstock_properties(feedstock_name, primary_df, fallback_df)
        if feedstock_props:
            feedstock_props['match_type'] = 'similar'
            feedstock_props['similar_group'] = group_name
            feedstock_props['original_crop'] = crop_name
            feedstock_props['original_residue'] = residue_type
            return feedstock_props
    
    return None


def _extract_feedstock_dict(row: pd.Series, source: str) -> Dict[str, Any]:
    """Extract feedstock properties from a DataFrame row."""
    result = {
        'source': source,
        'feedstock': str(row.get('Type', 'Unknown')),
        'origin': str(row.get('Origin', 'Unknown')) if 'Origin' in row else 'Unknown',
    }
    
    # Extract properties
    for prop_key, col_name in PROPERTY_COLUMNS.items():
        value = row.get(col_name)
        result[prop_key] = float(value) if pd.notna(value) else None
    
    # Extract challenges
    challenge_col = 'Soil Challenges to amend'
    if challenge_col in row and pd.notna(row[challenge_col]):
        challenges_str = str(row[challenge_col])
        result['challenges'] = [c.strip() for c in challenges_str.split(';')] if ';' in challenges_str else [challenges_str.strip()]
    else:
        result['challenges'] = []
    
    # Extract challenge flags
    result['challenge_flags'] = {
        col: bool(row[col]) if pd.notna(row.get(col)) else False
        for col in CHALLENGE_COLUMNS if col in row
    }
    
    # Extract other properties
    if 'Final Temperature' in row and pd.notna(row['Final Temperature']):
        result['temperature'] = float(row['Final Temperature'])
    if 'Biochar Yield (%)' in row and pd.notna(row['Biochar Yield (%)']):
        result['biochar_yield_pct'] = float(row['Biochar Yield (%)'])
    
    return result


def process_pyrolysis_data() -> Dict[str, Any]:
    """Main function to process and integrate pyrolysis data."""
    print("\n" + "="*60)
    print("Pyrolysis Data Integration")
    print("="*60)
    
    primary_df, fallback_df = load_pyrolysis_datasets()
    
    result = {
        'primary_df': None,
        'fallback_df': None,
        'primary_properties': {},
        'fallback_properties': {},
        'primary_ranges': {},
        'fallback_ranges': {},
        'primary_challenges': {},
        'fallback_challenges': {}
    }
    
    # Process primary dataset
    if primary_df is not None:
        print("\nProcessing primary dataset...")
        primary_df = clean_and_convert_types(primary_df)
        processed = _process_dataset(primary_df)
        result['primary_df'] = primary_df
        result['primary_properties'] = processed['properties']
        result['primary_ranges'] = processed['ranges']
        result['primary_challenges'] = processed['challenges']
        print(f"  Processed {len(primary_df)} rows")
        print(f"  Unique feedstocks: {primary_df['Type'].nunique() if 'Type' in primary_df.columns else 0}")
    
    # Process fallback dataset
    if fallback_df is not None:
        print("\nProcessing fallback dataset...")
        fallback_df = clean_and_convert_types(fallback_df)
        processed = _process_dataset(fallback_df)
        result['fallback_df'] = fallback_df
        result['fallback_properties'] = processed['properties']
        result['fallback_ranges'] = processed['ranges']
        result['fallback_challenges'] = processed['challenges']
        print(f"  Processed {len(fallback_df)} rows")
        print(f"  Unique feedstocks: {fallback_df['Type'].nunique() if 'Type' in fallback_df.columns else 0}")
    
    return result
