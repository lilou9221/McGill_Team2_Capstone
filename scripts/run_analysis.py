#!/usr/bin/env python
"""
Run the biochar suitability analysis pipeline.

Usage:
    python scripts/run_analysis.py [--lat LAT --lon LON --radius RADIUS]

Automatically installs PyYAML if missing, then delegates to src/main.py.
"""
import sys
import subprocess
from pathlib import Path

# Ensure PyYAML is installed
try:
    import yaml
except ImportError:
    print("Installing PyYAML...", file=sys.stderr, flush=True)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "pyyaml>=6.0", "--quiet"
    ])
    import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from src.main import main
    exit_code = main()
    sys.exit(exit_code)
