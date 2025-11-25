# Biochar Suitability Mapper

A precision soil health and crop residue intelligence tool for sustainable biochar application in Mato Grosso, Brazil.

## Core Features

### 1. Farmer Maps
Interactive soil health visualizations using H3 hexagonal grids:
- **Biochar Suitability Map** - Scores (0-10) showing where biochar application is most beneficial
- **Soil Organic Carbon Map** - SOC values (g/kg) across the region
- **Soil pH Map** - pH levels with diverging color scheme
- **Soil Moisture Map** - Volumetric moisture content

### 2. Investor Map
Municipality-level visualization of crop residue availability:
- Crop area (hectares)
- Crop production (tons)
- Available crop residue for biochar feedstock (tons/year)

### 3. Biochar Yield Calculator
Estimate biochar potential from major crops:
- Soybean, Maize, Sugarcane, Cotton
- Calculates residue per hectare based on yield
- Estimates biochar production using 30% pyrolysis yield

### 4. Biochar Recommendations
Feedstock suggestions based on soil conditions:
- Matches soil challenges to optimal biochar types
- Uses pyrolysis data for property matching
- Provides data-backed recommendations

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

**Windows Note:** Install geospatial libraries via Conda first:
```bash
conda install -c conda-forge geopandas rasterio shapely fiona pyproj gdal
pip install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run streamlit_app.py
```

The app will automatically download required data files from Google Drive on first run.

### 3. Use the Interface

- **Farmer Perspective**: View soil health maps, run analysis for specific locations
- **Investor Perspective**: Explore crop residue availability by municipality
- **Sourcing Tool**: Calculate biochar potential for specific crops

## Data Files

Data files are automatically downloaded from Google Drive. Required files:

| File | Description |
|------|-------------|
| `soil_moisture_res_250_sm_surface.tif` | Soil moisture |
| `SOC_res_250_b0.tif`, `SOC_res_250_b10.tif` | Soil organic carbon |
| `soil_pH_res_250_b0.tif`, `soil_pH_res_250_b10.tif` | Soil pH |
| `soil_temp_res_250_soil_temp_layer1.tif` | Soil temperature |
| `BR_Municipios_2024.*` | Municipality boundaries |
| `Updated_municipality_crop_production_data.csv` | Crop data |

All files are stored in the `data/` directory (flat structure).

## Command Line Usage

```bash
# Full state analysis
python src/main.py

# Specific location (100km radius)
python src/main.py --lat -15.5 --lon -56.0 --radius 100

# Custom H3 resolution
python src/main.py --lat -15.5 --lon -56.0 --h3-resolution 8
```

## Project Structure

```
biochar-mapper/
├── streamlit_app.py      # Main web application
├── src/
│   ├── main.py           # Core analysis pipeline
│   ├── analyzers/        # Suitability scoring, recommendations
│   ├── data_processors/  # Raster processing, H3 conversion
│   ├── map_generators/   # Map creation (suitability, SOC, pH, etc.)
│   └── utils/            # Caching, configuration, helpers
├── scripts/
│   ├── run_analysis.py   # Analysis wrapper
│   └── download_assets.py # Data download from Google Drive
├── data/
│   ├── pyrolysis/        # Biochar feedstock data
│   └── processed/        # Analysis outputs
├── output/html/          # Generated map files
└── configs/              # Configuration files
```

## Outputs

The analysis generates:

- **CSV Files** in `data/processed/`:
  - `suitability_scores.csv` - Biochar suitability scores (0-10 scale)
  - `merged_soil_data.csv` - Aggregated soil data by hexagon

- **HTML Maps** in `output/html/`:
  - `suitability_map.html` - Biochar suitability visualization
  - `soc_map_streamlit.html` - Soil organic carbon map
  - `ph_map_streamlit.html` - Soil pH map
  - `moisture_map_streamlit.html` - Soil moisture map

## Scoring System

Biochar suitability is calculated based on soil quality (see `SCORING_THRESHOLDS.md`):

| Property | Optimal Range | Weight |
|----------|--------------|--------|
| Moisture | 50-60% | 0.5 |
| SOC | >= 4% | 1.0 |
| pH | 6.0-7.0 | 0.7 |
| Temperature | 15-25C | 0.2 |

**Key principle:** Poor soil quality = Higher biochar suitability (inverse relationship)

## Troubleshooting

- **Missing data files**: The app downloads them automatically on first run
- **Analysis fails**: Ensure coordinates are within Mato Grosso (-7 to -18 lat, -50 to -62 lon)
- **Cache issues**: Delete `data/processed/cache/` to force regeneration

See `docs/TROUBLESHOOTING.md` for detailed solutions.

## License

McGill University Capstone Project - Residual Carbon Team
