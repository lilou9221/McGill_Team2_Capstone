# src/analyzers/biochar_recommender.py
"""
Biochar Recommender - Rule-Based Matching

Matches soil challenges to biochar feedstocks using processed pyrolysis data.
Focuses on 4 main crops: Coffee, Corn, Rice, Soybean.

This module handles BUSINESS LOGIC for recommendations:
- Identifies soil challenges from soil properties
- Matches challenges to feedstocks using rule-based logic
- Provides biochar recommendations

Data processing (loading, cleaning, type conversion) is handled by
pyrolysis_integrator.py - this module uses the processed data.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional

# Import data processing functions from integrator
from src.analyzers.pyrolysis_integrator import (
    process_pyrolysis_data,
    load_pyrolysis_datasets,
    clean_and_convert_types
)

# Focus on 4 main crops
MAIN_CROP_FEEDSTOCKS = {
    'Coffee': ['Coffee Silverskin', 'Spent Coffee Ground'],
    'Corn': ['Corn Straw', 'Corn cob'],
    'Rice': ['Rice Husk'],
    'Soybean': ['Soybean Straw']
}

# Soil challenge thresholds (based on SCORING_THRESHOLDS.md)
CHALLENGE_THRESHOLDS = {
    'Low OC': {'soc': 2.0, 'comparison': '<'},  # SOC < 2% is Poor/Very Poor
    'High pH': {'ph': 8.0, 'comparison': '>'},  # pH > 8.0 is Poor
    'Low pH': {'ph': 4.5, 'comparison': '<'},  # pH < 4.5 is Poor
    'High Temperature': {'temp': 30.0, 'comparison': '>'},  # temp > 30°C is Poor
    'Low Moisture': {'moisture': 30.0, 'comparison': '<'}  # moisture < 30% is Poor
}


def _load_processed_pyrolysis_data() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load and process pyrolysis datasets using the integrator module.
    
    This function uses pyrolysis_integrator to handle all data processing,
    then returns the cleaned DataFrames for business logic use.
    
    Returns
    -------
    Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]
        (primary_df, fallback_df) - Cleaned and processed DataFrames
    """
    # Use integrator to process data
    processed_data = process_pyrolysis_data()
    
    primary_df = processed_data.get('primary_df')
    fallback_df = processed_data.get('fallback_df')
    
    return primary_df, fallback_df


def identify_soil_challenges(
    soc: float,
    ph: float,
    moisture: float,
    temperature: float
) -> List[str]:
    """
    Identify soil challenges based on property values.
    
    Parameters
    ----------
    soc : float
        Soil Organic Carbon (%)
    ph : float
        Soil pH
    moisture : float
        Soil moisture (%)
    temperature : float
        Soil temperature (°C)
    
    Returns
    -------
    List[str]
        List of identified challenges
    """
    challenges = []
    
    # Check each challenge threshold
    if pd.notna(soc) and soc < CHALLENGE_THRESHOLDS['Low OC']['soc']:
        challenges.append('Low OC')
    
    if pd.notna(ph):
        if ph > CHALLENGE_THRESHOLDS['High pH']['ph']:
            challenges.append('High pH')
        elif ph < CHALLENGE_THRESHOLDS['Low pH']['ph']:
            challenges.append('Low pH')
    
    if pd.notna(temperature) and temperature > CHALLENGE_THRESHOLDS['High Temperature']['temp']:
        challenges.append('High Temperature')
    
    if pd.notna(moisture) and moisture < CHALLENGE_THRESHOLDS['Low Moisture']['moisture']:
        challenges.append('Low Moisture')
    
    return challenges


def find_matching_feedstocks(
    challenges: List[str],
    primary_df: Optional[pd.DataFrame],
    fallback_df: Optional[pd.DataFrame]
) -> Tuple[Optional[str], str, str, str]:
    """
    Find best matching feedstock for given soil challenges.
    
    Parameters
    ----------
    challenges : List[str]
        List of soil challenges
    primary_df : Optional[pd.DataFrame]
        Primary pyrolysis dataset
    fallback_df : Optional[pd.DataFrame]
        Fallback pyrolysis dataset
    
    Returns
    -------
    Tuple[Optional[str], str, str, str]
        (best_feedstock, reason, data_source, data_quality)
        - data_source: "experimental_data", "similar_feedstock", "provided_default", "general_default"
        - data_quality: "high", "medium", "low"
    """
    if not challenges:
        return None, "No soil challenges identified - soil is in good condition", "general_default", "low"
    
    # Try primary dataset first (focus on 4 main crops)
    if primary_df is not None and len(primary_df) > 0:
        # Score feedstocks by how many challenges they address
        scores = pd.Series([0] * len(primary_df), index=primary_df.index)
        
        for challenge in challenges:
            col_name = f'Challenge_{challenge.replace(" ", "_")}'
            if col_name in primary_df.columns:
                scores += primary_df[col_name].astype(int)
        
        # Filter to main crop feedstocks only
        main_feedstocks = []
        for crop_feedstocks in MAIN_CROP_FEEDSTOCKS.values():
            main_feedstocks.extend(crop_feedstocks)
        
        main_mask = primary_df['Type'].isin(main_feedstocks)
        if main_mask.any():
            # Get best match from main crops
            main_scores = scores[main_mask]
            if main_scores.max() > 0:
                best_idx = main_scores.idxmax()
                best_feedstock = primary_df.loc[best_idx, 'Type']
                match_count = int(main_scores.max())
                total_challenges = len(challenges)
                reason = f"Addresses {match_count}/{total_challenges} soil challenges: {', '.join(challenges)}"
                return best_feedstock, reason, "experimental_data", "high"
        
        # If no main crop match, use best overall match
        if scores.max() > 0:
            best_idx = scores.idxmax()
            best_feedstock = primary_df.loc[best_idx, 'Type']
            match_count = int(scores.max())
            total_challenges = len(challenges)
            reason = f"Addresses {match_count}/{total_challenges} soil challenges: {', '.join(challenges)} (fallback feedstock)"
            return best_feedstock, reason, "experimental_data", "high"
    
    # Try fallback dataset if primary didn't work
    if fallback_df is not None and len(fallback_df) > 0:
        # For fallback, use simple matching (no challenge columns)
        # Just return a generic recommendation
        reason = f"Soil challenges identified: {', '.join(challenges)}. Using fallback dataset (limited challenge matching available)."
        return "See pyrolysis data", reason, "experimental_data", "high"
    
    # No data available
    return None, f"Soil challenges identified: {', '.join(challenges)}. Pyrolysis data not available for recommendations.", "general_default", "low"


def recommend_biochar(hex_df: pd.DataFrame) -> pd.DataFrame:
    """
    Recommend biochar feedstocks based on soil challenges.
    
    Identifies soil challenges from soil properties and matches them to
    biochar feedstocks using rule-based logic. Focuses on 4 main crops:
    Coffee, Corn, Rice, Soybean.
    
    Parameters
    ----------
    hex_df : pd.DataFrame
        DataFrame with soil properties and suitability scores.
        Must have columns: mean_soc, mean_ph, mean_moisture, mean_temperature
        (or similar property columns)
    
    Returns
    -------
    pd.DataFrame
        DataFrame with added columns:
        - Recommended_Feedstock: str
        - Recommendation_Reason: str
    """
    print("\n" + "="*60)
    print("Biochar Recommendation System")
    print("="*60)
    
    # Load processed pyrolysis data (uses integrator for data processing)
    primary_df, fallback_df = _load_processed_pyrolysis_data()
    
    if primary_df is None and fallback_df is None:
        print("  Error: No pyrolysis data available")
        hex_df["Recommended_Feedstock"] = "Data unavailable"
        hex_df["Recommendation_Reason"] = "Pyrolysis datasets not found"
        return hex_df
    
    # Find property columns (handle different naming conventions)
    # Try to find columns with 'mean' prefix first, then fall back to any matching column
    soc_col = (next((c for c in hex_df.columns if 'soc' in c.lower() and 'mean' in c.lower()), None) or
               next((c for c in hex_df.columns if 'soc' in c.lower() and c.lower() not in ['biochar_suitability_score']), None))
    ph_col = (next((c for c in hex_df.columns if 'ph' in c.lower() and 'mean' in c.lower()), None) or
              next((c for c in hex_df.columns if 'ph' in c.lower() and c.lower() not in ['biochar_suitability_score']), None))
    moisture_col = (next((c for c in hex_df.columns if 'moisture' in c.lower() and 'mean' in c.lower()), None) or
                    next((c for c in hex_df.columns if 'moisture' in c.lower() or 'sm_surface' in c.lower()), None))
    temp_col = (next((c for c in hex_df.columns if ('temp' in c.lower() or 'temperature' in c.lower()) and 'mean' in c.lower()), None) or
                next((c for c in hex_df.columns if 'temp' in c.lower() or 'temperature' in c.lower()), None))
    
    if not soc_col or not ph_col:
        print("  Warning: Missing required columns (SOC or pH)")
        hex_df["Recommended_Feedstock"] = "Insufficient data"
        hex_df["Recommendation_Reason"] = "Missing SOC or pH data for challenge identification"
        return hex_df
    
    print(f"  Using columns: SOC={soc_col}, pH={ph_col}, Moisture={moisture_col}, Temp={temp_col}")
    
    # Vectorized processing for better performance
    hex_df = hex_df.copy()
    
    # Get property values with defaults
    soc_values = hex_df[soc_col] if soc_col else pd.Series([np.nan] * len(hex_df))
    ph_values = hex_df[ph_col] if ph_col else pd.Series([np.nan] * len(hex_df))
    moisture_values = hex_df[moisture_col].fillna(50.0) if moisture_col else pd.Series([50.0] * len(hex_df))
    temp_values = hex_df[temp_col].fillna(20.0) if temp_col else pd.Series([20.0] * len(hex_df))
    
    # Pre-compute challenge columns (vectorized)
    has_low_oc = (soc_values < CHALLENGE_THRESHOLDS['Low OC']['soc']).fillna(False)
    has_high_ph = (ph_values > CHALLENGE_THRESHOLDS['High pH']['ph']).fillna(False)
    has_low_ph = (ph_values < CHALLENGE_THRESHOLDS['Low pH']['ph']).fillna(False)
    has_high_temp = (temp_values > CHALLENGE_THRESHOLDS['High Temperature']['temp']).fillna(False)
    has_low_moisture = (moisture_values < CHALLENGE_THRESHOLDS['Low Moisture']['moisture']).fillna(False)
    
    # Build challenge lists efficiently
    challenge_lists = []
    for i in range(len(hex_df)):
        challenges = []
        if has_low_oc.iloc[i]:
            challenges.append('Low OC')
        if has_high_ph.iloc[i]:
            challenges.append('High pH')
        if has_low_ph.iloc[i]:
            challenges.append('Low pH')
        if has_high_temp.iloc[i]:
            challenges.append('High Temperature')
        if has_low_moisture.iloc[i]:
            challenges.append('Low Moisture')
        challenge_lists.append(challenges)
    
    # Optimized batch processing
    recommended_feedstocks = []
    recommendation_reasons = []
    data_sources = []
    data_qualities = []
    
    # Import similar feedstock grouping function
    from src.analyzers.pyrolysis_integrator import find_similar_feedstock, get_feedstock_for_crop
    
    # Pre-compute feedstock scores if primary_df available
    if primary_df is not None and len(primary_df) > 0:
        # Get main crop feedstocks list
        main_feedstocks = []
        for crop_feedstocks in MAIN_CROP_FEEDSTOCKS.values():
            main_feedstocks.extend(crop_feedstocks)
        
        # Pre-compute challenge column names
        challenge_col_map = {
            'Low OC': 'Challenge_Low_OC',
            'High pH': 'Challenge_High_pH',
            'Low pH': 'Challenge_Low_pH',
            'High Temperature': 'Challenge_High_Temperature',
            'Low Moisture': 'Challenge_Low_Moisture'
        }
        
        # Process all rows (optimized with pre-computed lookups)
        for i, challenges in enumerate(challenge_lists):
            if not challenges:
                recommended_feedstocks.append("No recommendation")
                recommendation_reasons.append("No soil challenges identified - soil is in good condition")
                data_sources.append("general_default")
                data_qualities.append("low")
                continue
            
            # Score feedstocks by how many challenges they address (vectorized)
            scores = pd.Series([0] * len(primary_df), index=primary_df.index, dtype=int)
            for challenge in challenges:
                col_name = challenge_col_map.get(challenge)
                if col_name and col_name in primary_df.columns:
                    scores += primary_df[col_name].astype(int)
            
            # Filter to main crop feedstocks first
            main_mask = primary_df['Type'].isin(main_feedstocks)
            if main_mask.any():
                main_scores = scores[main_mask]
                if main_scores.max() > 0:
                    best_idx = main_scores.idxmax()
                    best_feedstock = primary_df.loc[best_idx, 'Type']
                    match_count = int(main_scores.max())
                    total_challenges = len(challenges)
                    recommended_feedstocks.append(best_feedstock)
                    recommendation_reasons.append(f"Addresses {match_count}/{total_challenges} soil challenges: {', '.join(challenges)}")
                    data_sources.append("experimental_data")
                    data_qualities.append("high")
                    continue
            
            # If no main crop match, use best overall
            if scores.max() > 0:
                best_idx = scores.idxmax()
                best_feedstock = primary_df.loc[best_idx, 'Type']
                match_count = int(scores.max())
                total_challenges = len(challenges)
                recommended_feedstocks.append(best_feedstock)
                recommendation_reasons.append(f"Addresses {match_count}/{total_challenges} soil challenges: {', '.join(challenges)} (fallback feedstock)")
                data_sources.append("experimental_data")
                data_qualities.append("high")
            else:
                # Try fallback dataset if available
                if fallback_df is not None and len(fallback_df) > 0:
                    # Fallback dataset doesn't have challenge columns, but we can still recommend
                    # a feedstock from the fallback dataset (prefer main crop feedstocks if available)
                    fallback_main_mask = fallback_df['Type'].isin(main_feedstocks)
                    if fallback_main_mask.any():
                        # Use first main crop feedstock from fallback
                        fallback_feedstock = fallback_df[fallback_main_mask]['Type'].iloc[0]
                        recommended_feedstocks.append(fallback_feedstock)
                        recommendation_reasons.append(f"Soil challenges identified: {', '.join(challenges)}. Using fallback dataset feedstock (limited challenge matching).")
                        data_sources.append("experimental_data")
                        data_qualities.append("high")
                    else:
                        # Use first available feedstock from fallback
                        fallback_feedstock = fallback_df['Type'].iloc[0]
                        recommended_feedstocks.append(fallback_feedstock)
                        recommendation_reasons.append(f"Soil challenges identified: {', '.join(challenges)}. Using fallback dataset feedstock (limited challenge matching).")
                        data_sources.append("experimental_data")
                        data_qualities.append("high")
                else:
                    # No data available
                    recommended_feedstocks.append("No recommendation")
                    recommendation_reasons.append(f"Soil challenges identified: {', '.join(challenges)}. No matching feedstock found.")
                    data_sources.append("general_default")
                    data_qualities.append("low")
    else:
        # Fallback dataset or no data
        for challenges in challenge_lists:
            if not challenges:
                recommended_feedstocks.append("No recommendation")
                recommendation_reasons.append("No soil challenges identified - soil is in good condition")
                data_sources.append("general_default")
                data_qualities.append("low")
            else:
                # Try fallback dataset
                if fallback_df is not None and len(fallback_df) > 0:
                    # Prefer main crop feedstocks from fallback if available
                    main_feedstocks = []
                    for crop_feedstocks in MAIN_CROP_FEEDSTOCKS.values():
                        main_feedstocks.extend(crop_feedstocks)
                    
                    fallback_main_mask = fallback_df['Type'].isin(main_feedstocks)
                    if fallback_main_mask.any():
                        # Use first main crop feedstock from fallback
                        fallback_feedstock = fallback_df[fallback_main_mask]['Type'].iloc[0]
                        recommended_feedstocks.append(fallback_feedstock)
                        recommendation_reasons.append(f"Soil challenges identified: {', '.join(challenges)}. Using fallback dataset feedstock (limited challenge matching available).")
                        data_sources.append("experimental_data")
                        data_qualities.append("high")
                    else:
                        # Use first available feedstock from fallback
                        fallback_feedstock = fallback_df['Type'].iloc[0]
                        recommended_feedstocks.append(fallback_feedstock)
                        recommendation_reasons.append(f"Soil challenges identified: {', '.join(challenges)}. Using fallback dataset feedstock (limited challenge matching available).")
                        data_sources.append("experimental_data")
                        data_qualities.append("high")
                else:
                    recommended_feedstocks.append("See pyrolysis data")
                    recommendation_reasons.append(f"Soil challenges identified: {', '.join(challenges)}. Pyrolysis data not available for recommendations.")
                    data_sources.append("general_default")
                    data_qualities.append("low")
    
    # Add columns to DataFrame
    hex_df["Recommended_Feedstock"] = recommended_feedstocks
    hex_df["Recommendation_Reason"] = recommendation_reasons
    hex_df["Data_Source"] = data_sources
    hex_df["Data_Quality"] = data_qualities
    
    # Print summary
    unique_feedstocks = hex_df["Recommended_Feedstock"].value_counts()
    print(f"\n  Recommendation summary:")
    for feedstock, count in unique_feedstocks.head(10).items():
        print(f"    {feedstock}: {count} locations")
    
    return hex_df
