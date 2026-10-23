"""Command-line entry point for forest analytics."""

import argparse

from .pipeline import analyze_cloud


def main() -> None:
    """Analyze an NPY point cloud and write results."""
    parser = argparse.ArgumentParser()
    parser.add_argument("cloud")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    analyze_cloud(args.cloud, args.config, args.out)
