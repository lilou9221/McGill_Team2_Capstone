# Developer Reference: Data Flow Memory Map

This folder contains architecture documentation for developers working on the Biochar Suitability Mapper.

## Quick Reference

The application has **4 core features**:

| Feature | Data Source | Output |
|---------|-------------|--------|
| **Farmer Maps** | GeoTIFF soil data | suitability_map.html, soc_map.html, ph_map.html, moisture_map.html |
| **Investor Map** | Municipality boundaries + Crop CSV | investor_crop_area_map.html |
| **Biochar Yield Calculator** | residue_ratios.csv + crop data | In-app calculation |
| **Biochar Recommendations** | pyrolysis/*.csv + soil scores | In-app recommendations |

## Files

- **memory_map.py** - Generates the data flow diagram
- **data_flow_memory_map.png** - Visual flowchart of the processing pipeline

## Regenerate Diagram

```bash
cd memory_map
python memory_map.py
```

## Pipeline Overview

```
GeoTIFF Files (data/*.tif)
    |
    v
clip_all_rasters_to_circle (raster_clip.py)
    |
    v
convert_all_rasters_to_dataframes (raster_to_csv.py)
    |
    v
process_dataframes_with_h3 (h3_converter.py)
    |
    v
merge_and_aggregate_soil_data (suitability.py)
    |
    +---> merged_soil_data.csv
    |         |
    |         +---> create_soc_map (soc_map.py) --> soc_map.html
    |         +---> create_ph_map (ph_map.py) --> ph_map.html
    |         +---> create_moisture_map (moisture_map.py) --> moisture_map.html
    |
    v
calculate_biochar_suitability_scores (biochar_suitability.py)
    |
    v
suitability_scores.csv
    |
    v
create_biochar_suitability_map (biochar_map.py) --> suitability_map.html
```

**Investor Map (separate pipeline):**
```
Municipality Boundaries + Crop CSV
    |
    v
prepare_investor_crop_area_geodata (municipality_waste_map.py)
    |
    v
create_municipality_waste_deck --> investor_crop_area_map.html
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `src/main.py` | Main pipeline orchestration |
| `src/analyzers/biochar_suitability.py` | Suitability score calculation |
| `src/analyzers/biochar_recommender.py` | Feedstock recommendations |
| `src/data_processors/raster_clip.py` | GeoTIFF clipping |
| `src/data_processors/h3_converter.py` | H3 hexagonal indexing |
| `src/map_generators/*.py` | Map generation |
| `src/utils/cache.py` | Caching system |
| `streamlit_app.py` | Web interface |

## Diagram Legend

- **Light Blue Boxes**: Files/Data
- **Light Orange Boxes**: Processes/Functions  
- **Light Green Boxes**: Final Map Outputs
- **Arrows**: Data flow direction
