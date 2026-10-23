"""Command-line entry point for forest analytics.

    canopy-analyze data/raw/plot.las --out results/plot
    canopy-analyze map.npy --config my.yaml --out results/try
"""

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    """Analyse a point cloud (.npy, .ply, .pcd, .las/.laz, .txt/.xyz) and write results."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("cloud", type=Path)
    parser.add_argument("--config", type=Path, help="YAML settings (default: configs/default.yaml)")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.config:
        # Must happen before canopy modules are imported: they read defaults on import.
        os.environ["CANOPY_CONFIG"] = str(args.config.resolve())
    from .pipeline import analyze_cloud

    print(json.dumps(analyze_cloud(args.cloud, args.out), indent=2))
