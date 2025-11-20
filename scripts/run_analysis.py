#!/usr/bin/env python
"""
Wrapper script to ensure dependencies are installed before running the analysis pipeline.
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
