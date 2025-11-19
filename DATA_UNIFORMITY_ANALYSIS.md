# Data Uniformity Analysis

## Purpose

This analysis checks if any soil property data is abnormally uniform (>80% of values in the same range), which could explain why suitability scores cluster around certain values (like 51.4).

## How to Run

After running the main pipeline, execute:

```bash
python tests/check_uniformity_comprehensive.py
```

This will analyze the merged data and identify any properties with >80% uniformity.

## What to Look For

### Indicators of Uniformity

1. **>80% of data in one bin** - When dividing the data range into 10 equal bins, if one bin contains >80% of values
2. **>80% identical values** - If a single value appears in >80% of rows
3. **Very low coefficient of variation** - CV < 5% suggests very little variation
4. **Few unique values** - If there are very few unique values compared to total rows

### Properties to Check

1. **Soil Moisture** - Check if values cluster around default (50%) or in a narrow range
2. **Soil Temperature** - Check if values cluster around default (20°C) or in a narrow range  
3. **Soil Organic Carbon (SOC)** - Check if values are very similar across the region
4. **Soil pH** - Check if pH values are uniform

### Expected Issues

Based on the scoring system, if data is uniform:

- **Uniform SOC values** - If most SOC values are the same (e.g., all around 1.5%), this would give similar scores
- **Uniform pH values** - If most pH values are similar (e.g., all around 6.0), this would give similar scores
- **Default moisture/temperature** - If many values are using defaults (50% moisture, 20°C temp), this would cluster scores

### Score Clustering Explanation

If scores cluster around 51.4 (5.14 on 0-10 scale), this suggests:

- **Soil Quality Index ≈ 48.6** (100 - 51.4 = 48.6)
- This corresponds to a **Total Weighted Score ≈ 3.5** (48.6 / 100 × 7.2 = 3.5)

This could happen if:
- Most properties are rated as "Poor" or "Moderate" (scores 1-2)
- With weights: Moisture(0.5) + SOC(1.0) + pH(0.7) + Temp(0.2) = 2.4
- If all properties score 1-2, weighted total ≈ 2.4-4.8
- This gives Soil Quality Index ≈ 33-67, Biochar Suitability ≈ 33-67

## Analysis Scripts

1. **`tests/check_uniformity_comprehensive.py`** - Full analysis of processed data
2. **`tests/analyze_data_uniformity.py`** - Sample analysis from raw files

## Next Steps

1. Run the main pipeline to generate processed data
2. Run the uniformity analysis script
3. Check which properties show >80% uniformity
4. Investigate why those properties are uniform (data quality, defaults, actual uniformity)


