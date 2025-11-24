# Streamlit Cloud Deployment Notes

## External data source

All heavy datasets (GeoTIFFs, boundary shapefiles, crop production CSV) are now hosted in a shared Google Drive folder:

- **Folder name:** `McGill_Team2_Capstone_Residual_Carbon`
- **Folder URL:** https://drive.google.com/drive/u/1/folders/1FvG4FM__Eam2pXggHdo5piV7gg2bljjt

Keeping data in Drive removes the Git LFS bandwidth/storage bottleneck and allows Streamlit Cloud to pull the assets on demand.

## Download script

The repository ships with `scripts/download_assets.py`, which uses `gdown` to pull the Drive folder and copy the required files into the local `data/` directory. The script runs automatically from the Streamlit app when files are missing, but you can trigger it manually:

```bash
pip install -r requirements.txt  # ensures gdown is available
python scripts/download_assets.py
```

Use `python scripts/download_assets.py --force` to re-download and overwrite existing files.

## Required files pulled from Drive

```
data/boundaries/BR_Municipios_2024/BR_Municipios_2024.{shp, dbf, shx, prj, cpg}
data/crop_data/Updated_municipality_crop_production_data.csv
data/raw/SOC_res_250_b0.tif
data/raw/SOC_res_250_b10.tif
data/raw/soil_moisture_res_250_sm_surface.tif
data/raw/soil_pH_res_250_b0.tif
data/raw/soil_pH_res_250_b10.tif
data/raw/soil_temp_res_250_soil_temp_layer1.tif
```

The Drive folder mirrors the repository layout (`data/...`), so the script can copy files directly into place.

## Streamlit Cloud deployment workflow

1. **Connect the repo:** `https://github.com/lilou9221/mcgill_team2_capstone`.
2. **Set credentials/environment variables** (if any) in Streamlit Cloud.
3. **Deploy:** the app will call `scripts/download_assets.py` automatically on first run. Allow a few minutes for the initial download (~400 MB).
4. **Subsequent restarts** reuse the cached data directory, so downloads run only when files are missing.

## Local development workflow

1. Clone the repo.
2. Run `python scripts/download_assets.py` once to fetch the datasets.
3. Launch the Streamlit app as usual.

> If the download fails, verify that the Drive folder link is public (“Anyone with the link can view”) and that `gdown` is installed.
