#!/usr/bin/env python
"""
Download required GeoTIFF and shapefile assets from Google Drive.

Usage:
    python scripts/download_assets.py

Optional flags:
    --force    Re-download and overwrite existing files.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

try:
    import gdown
except ImportError as exc:  # pragma: no cover - handled during runtime
    raise SystemExit(
        "gdown is required. Install dependencies via `pip install -r requirements.txt`."
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOOGLE_DRIVE_FOLDER_ID = "1FvG4FM__Eam2pXggHdo5piV7gg2bljjt"
GOOGLE_DRIVE_URL = f"https://drive.google.com/drive/folders/{GOOGLE_DRIVE_FOLDER_ID}"

REQUIRED_FILES = [
    {
        "filename": "BR_Municipios_2024.shp",
        "target": "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.shp",
    },
    {
        "filename": "BR_Municipios_2024.dbf",
        "target": "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.dbf",
    },
    {
        "filename": "BR_Municipios_2024.shx",
        "target": "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.shx",
    },
    {
        "filename": "BR_Municipios_2024.prj",
        "target": "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.prj",
    },
    {
        "filename": "BR_Municipios_2024.cpg",
        "target": "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.cpg",
    },
    {
        "filename": "Updated_municipality_crop_production_data.csv",
        "target": "data/crop_data/Updated_municipality_crop_production_data.csv",
    },
    {"filename": "SOC_res_250_b0.tif", "target": "data/raw/SOC_res_250_b0.tif"},
    {"filename": "SOC_res_250_b10.tif", "target": "data/raw/SOC_res_250_b10.tif"},
    {
        "filename": "soil_moisture_res_250_sm_surface.tif",
        "target": "data/raw/soil_moisture_res_250_sm_surface.tif",
    },
    {"filename": "soil_pH_res_250_b0.tif", "target": "data/raw/soil_pH_res_250_b0.tif"},
    {"filename": "soil_pH_res_250_b10.tif", "target": "data/raw/soil_pH_res_250_b10.tif"},
    {
        "filename": "soil_temp_res_250_soil_temp_layer1.tif",
        "target": "data/raw/soil_temp_res_250_soil_temp_layer1.tif",
    },
]


def _download_drive_folder(tmp_dir: Path) -> Path:
    """Download the shared Drive folder into a temp directory and return its root."""
    output_dir = tmp_dir / "drive_download"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        gdown.download_folder(
            id=GOOGLE_DRIVE_FOLDER_ID,
            output=str(output_dir),
            quiet=False,
            use_cookies=False,
            remaining_ok=True,
        )
    except Exception as e:
        print(f"[ERROR] Failed to download folder: {e}", file=sys.stderr)
        raise
    
    # gdown may create a subdirectory with the folder name, or put files directly in output_dir
    # Check for subdirectories first
    subdirs = [p for p in output_dir.iterdir() if p.is_dir()]
    if len(subdirs) == 1:
        return subdirs[0]
    # If no subdir, files might be directly in output_dir
    files = [p for p in output_dir.iterdir() if p.is_file()]
    if files:
        return output_dir
    
    raise FileNotFoundError(f"No files found in downloaded folder: {output_dir}")


def _locate_source_file(source_root: Path, filename: str) -> Path | None:
    """Find a file inside the downloaded Drive folder by name."""
    matches = list(source_root.rglob(filename))
    if not matches:
        return None
    # Prefer the shallowest match (in case of duplicates)
    return sorted(matches, key=lambda p: len(p.parts))[0]


def _copy_required_assets(source_root: Path, force: bool) -> tuple[list[Path], list[Path]]:
    """Copy required assets from source to destination.
    
    Returns:
        Tuple of (copied_files, missing_files)
    """
    missing_sources = []
    copied_files = []
    
    print(f"[INFO] Searching for files in: {source_root}")
    print(f"[INFO] Found {len(list(source_root.rglob('*')))} items in downloaded folder")
    
    for file_spec in REQUIRED_FILES:
        rel_target = Path(file_spec["target"])
        dest = PROJECT_ROOT / rel_target
        src = _locate_source_file(source_root, file_spec["filename"])

        if src is None:
            print(f"[WARN] File not found in Drive: {file_spec['filename']}", file=sys.stderr)
            missing_sources.append(rel_target)
            continue

        if dest.exists() and not force:
            print(f"[SKIP] Already exists: {rel_target}")
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dest)
            print(f"[OK] Copied {rel_target}")
            copied_files.append(rel_target)
        except Exception as e:
            print(f"[ERROR] Failed to copy {rel_target}: {e}", file=sys.stderr)
            missing_sources.append(rel_target)

    return copied_files, missing_sources


def download_assets(force: bool = False) -> int:
    """Download assets if any required file is missing."""
    existing = [
        PROJECT_ROOT / file_spec["target"]
        for file_spec in REQUIRED_FILES
        if (PROJECT_ROOT / file_spec["target"]).exists()
    ]
    if len(existing) == len(REQUIRED_FILES) and not force:
        print("All required data files are already present. Nothing to do.")
        return 0

    print(f"Downloading assets from {GOOGLE_DRIVE_URL} ...")
    print(f"Looking for {len(REQUIRED_FILES)} required files...")
    
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            drive_root = _download_drive_folder(Path(tmp_dir))
            copied, missing = _copy_required_assets(drive_root, force=force)
            
            if missing:
                print(f"\n[ERROR] {len(missing)} files are still missing:", file=sys.stderr)
                for m in missing:
                    print(f"  - {m}", file=sys.stderr)
                return 1
            
            if copied:
                print(f"\n[SUCCESS] Downloaded {len(copied)} files successfully.")
            else:
                print("\n[INFO] No new files downloaded (all already exist).")
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1

    print("Data download complete.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Download project data assets from Google Drive.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite existing files.",
    )
    args = parser.parse_args()
    return download_assets(force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())

