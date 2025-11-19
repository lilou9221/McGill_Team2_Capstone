# Biochar Suitability Scoring Thresholds and Ranges

## Overview

The biochar suitability scoring system evaluates soil quality based on four properties:
1. **Soil Moisture** (%)
2. **Soil Organic Carbon (SOC)** (%)
3. **Soil pH**
4. **Soil Temperature** (°C)

**Key Principle**: Biochar is most beneficial in poor soils, so **lower soil quality = higher biochar suitability**.

---

## Property Rating System

Each property is rated on a 4-level scale (0-3):
- **0 = Very Poor**
- **1 = Poor**
- **2 = Moderate**
- **3 = Good**

### 1. Soil Moisture (%)

**Input**: Soil moisture percentage (0-100%)

| Range | Score | Rating |
|-------|-------|--------|
| < 20% or > 80% | 0 | Very Poor |
| 20% ≤ moisture < 30% or 70% < moisture ≤ 80% | 1 | Poor |
| 30% ≤ moisture < 50% or 60% < moisture ≤ 70% | 2 | Moderate |
| 50% ≤ moisture ≤ 60% | 3 | Good |

**Optimal Range**: 50-60%

**Default Value** (if missing): 50% (moderate)

---

### 2. Soil Organic Carbon (SOC) (%)

**Input**: SOC percentage

| Range | Score | Rating |
|-------|-------|--------|
| < 1% | 0 | Very Poor |
| 1% ≤ SOC < 2% | 1 | Poor |
| 2% ≤ SOC < 4% | 2 | Moderate |
| ≥ 4% | 3 | Good |

**Optimal Range**: ≥ 4%

**Required**: Yes (calculation skipped if missing)

---

### 3. Soil pH

**Input**: pH value (0-14)

| Range | Score | Rating |
|-------|-------|--------|
| < 3.0 or > 9.0 | 0 | Very Poor |
| 3.0 ≤ pH < 4.5 or 8.0 < pH ≤ 9.0 | 1 | Poor |
| 4.5 ≤ pH < 6.0 or 7.0 < pH ≤ 8.0 | 2 | Moderate |
| 6.0 ≤ pH ≤ 7.0 | 3 | Good |

**Optimal Range**: 6.0-7.0

**Required**: Yes (calculation skipped if missing)

---

### 4. Soil Temperature (°C)

**Input**: Temperature in Celsius

| Range | Score | Rating |
|-------|-------|--------|
| < 0°C or > 35°C | 0 | Very Poor |
| 0°C ≤ temp < 10°C or 30°C < temp ≤ 35°C | 1 | Poor |
| 10°C ≤ temp < 15°C or 25°C < temp ≤ 30°C | 2 | Moderate |
| 15°C ≤ temp ≤ 25°C | 3 | Good |

**Optimal Range**: 15-25°C

**Default Value** (if missing): 20°C (good)

---

## Weighted Scoring System

Each property is weighted differently:

| Property | Weight | Maximum Weighted Score |
|----------|--------|------------------------|
| Moisture | 0.5 | 1.5 (3 × 0.5) |
| SOC | 1.0 | 3.0 (3 × 1.0) |
| pH | 0.7 | 2.1 (3 × 0.7) |
| Temperature | 0.2 | 0.6 (3 × 0.2) |
| **Total** | **2.4** | **7.2** |

**Calculation**:
- Weighted Score = Property Score × Weight
- Total Weighted Score = Sum of all weighted scores
- Maximum Possible Score = 7.2

---

## Final Scores

### Soil Quality Index (0-100)

```
Soil Quality Index = (Total Weighted Score / 7.2) × 100
```

- **0-25**: Very Poor Soil
- **26-50**: Poor Soil
- **51-75**: Moderate Soil
- **76-100**: Good Soil

### Biochar Suitability Score (0-100)

```
Biochar Suitability Score = 100 - Soil Quality Index
```

**Inverse Relationship**: Lower soil quality = Higher biochar suitability

| Biochar Suitability Score | Grade | Color Hex | Recommendation |
|---------------------------|-------|-----------|----------------|
| ≥ 76 | High Suitability | #d32f2f (Red) | Very suitable – biochar highly recommended |
| 51-75 | Moderate Suitability | #f57c00 (Orange) | Suitable – biochar recommended |
| 26-50 | Low Suitability | #fbc02d (Yellow) | Marginal – biochar may help |
| < 26 | Not Suitable | #388e3c (Green) | Healthy soil – biochar not needed |

---

## Unit Conversions

### Moisture Conversion
- **Input**: m³/m³ (from SMAP data)
- **Output**: Percentage (0-100%)
- **Formula**: `moisture_percent = moisture_m3_m3 × 100`

### SOC Conversion
- **Input**: g/kg (from soil data)
- **Output**: Percentage
- **Formula**: `soc_percent = soc_g_kg / 10.0`

### Temperature Conversion
- **Input**: Kelvin (K) (from SMAP data)
- **Output**: Celsius (°C)
- **Formula**: `temp_celsius = temp_kelvin - 273.15`

### pH
- **Input**: Already in pH units (no conversion needed)

---

## Default Values

When data is missing:
- **Moisture**: 50% (moderate)
- **Temperature**: 20°C (good)
- **SOC**: **Required** - calculation skipped if missing
- **pH**: **Required** - calculation skipped if missing

---

## Example Calculations

### Example 1: Poor Soil (High Biochar Suitability)
- Moisture: 15% → Score: 0 (Very Poor) → Weighted: 0.0
- SOC: 0.8% → Score: 0 (Very Poor) → Weighted: 0.0
- pH: 5.0 → Score: 2 (Moderate) → Weighted: 1.4
- Temperature: 32°C → Score: 1 (Poor) → Weighted: 0.2

**Total Weighted Score**: 1.6
**Soil Quality Index**: (1.6 / 7.2) × 100 = 22.2
**Biochar Suitability Score**: 100 - 22.2 = **77.8** (High Suitability)

### Example 2: Good Soil (Low Biochar Suitability)
- Moisture: 55% → Score: 3 (Good) → Weighted: 1.5
- SOC: 5.0% → Score: 3 (Good) → Weighted: 3.0
- pH: 6.5 → Score: 3 (Good) → Weighted: 2.1
- Temperature: 20°C → Score: 3 (Good) → Weighted: 0.6

**Total Weighted Score**: 7.2
**Soil Quality Index**: (7.2 / 7.2) × 100 = 100.0
**Biochar Suitability Score**: 100 - 100.0 = **0.0** (Not Suitable)

---

## Notes

1. **SOC and pH are required** - rows without these values are skipped
2. **Moisture and Temperature have defaults** - missing values use defaults (50% and 20°C)
3. **Score ranges are inclusive** - e.g., "50% ≤ moisture ≤ 60%" includes both 50% and 60%
4. **Biochar suitability is inverse to soil quality** - the worse the soil, the more biochar is needed
5. **Final scores are rounded to 2 decimal places**


