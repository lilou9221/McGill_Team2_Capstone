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
    "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.shp",
    "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.dbf",
    "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.shx",
    "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.prj",
    "data/boundaries/BR_Municipios_2024/BR_Municipios_2024.cpg",
    "data/crop_data/Updated_municipality_crop_production_data.csv",
    "data/raw/SOC_res_250_b0.tif",
    "data/raw/SOC_res_250_b10.tif",
    "data/raw/soil_moisture_res_250_sm_surface.tif",
    "data/raw/soil_pH_res_250_b0.tif",
    "data/raw/soil_pH_res_250_b10.tif",
    "data/raw/soil_temp_res_250_soil_temp_layer1.tif",
]


def _download_drive_folder(tmp_dir: Path) -> Path:
    """Download the shared Drive folder into a temp directory and return its root."""
    output_dir = tmp_dir / "drive_download"
    output_dir.mkdir(parents=True, exist_ok=True)
    gdown.download_folder(
        id=GOOGLE_DRIVE_FOLDER_ID,
        output=str(output_dir),
        quiet=False,
        use_cookies=False,
        remaining_ok=True,
    )
    # gdown creates the folder name as a child of output_dir
    subdirs = [p for p in output_dir.iterdir() if p.is_dir()]
    if len(subdirs) == 1:
        return subdirs[0]
    return output_dir


def _copy_required_assets(source_root: Path, force: bool) -> None:
    missing_sources = []
    for rel_path in REQUIRED_FILES:
        src = source_root / rel_path
        dest = PROJECT_ROOT / rel_path

        if not src.exists():
            missing_sources.append(rel_path)
            continue

        if dest.exists() and not force:
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"[OK] Copied {rel_path}")

    if missing_sources:
        print(
            "[WARN] The following files were not found in the Google Drive folder:",
            *missing_sources,
            sep="\n  ",
            file=sys.stderr,
        )


def download_assets(force: bool = False) -> int:
    """Download assets if any required file is missing."""
    existing = [PROJECT_ROOT / rel for rel in REQUIRED_FILES if (PROJECT_ROOT / rel).exists()]
    if len(existing) == len(REQUIRED_FILES) and not force:
        print("All required data files are already present. Nothing to do.")
        return 0

    print(f"Downloading assets from {GOOGLE_DRIVE_URL} ...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        drive_root = _download_drive_folder(Path(tmp_dir))
        _copy_required_assets(drive_root, force=force)

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

