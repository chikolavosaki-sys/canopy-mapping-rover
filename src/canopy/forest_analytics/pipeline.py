"""Configuration-driven forest analytics pipeline."""

import csv
import json
from pathlib import Path

import numpy as np
import yaml

from canopy.io import load_points

from .density import density_grid
from .ground import normalize_heights
from .ladder_fuel import ladder_fuel_index, save_ladder_report
from .stems import detect_stems, stems_to_rows


def analyze_cloud(cloud_path: str | Path, config_path: str | Path, out_dir: str | Path) -> dict:
    """Run ground normalization, density, ladder proxy, and stem detection."""
    config = yaml.safe_load(Path(config_path).read_text())
    points = load_points(cloud_path)
    ground = config["ground"]
    _, normalized = normalize_heights(
        points, ground["grid_size_m"], ground["lowest_quantile"]
    )
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    np.save(destination / "normalised_cloud.npy", normalized)
    density = density_grid(
        normalized,
        tuple(tuple(band) for band in config["density"]["bands_m"]),
        config["density"]["grid_size_m"],
        config["voxel_size_m"],
    )
    np.save(destination / "density.npy", density.occupancy)
    ladder = config["ladder_fuel"]
    score, origin = ladder_fuel_index(
        normalized,
        ladder["grid_size_m"],
        ladder["occupancy_voxel_m"],
        tuple(tuple(band) for band in ladder["bands_m"]),
        tuple(ladder["band_weights"]),
    )
    save_ladder_report(score, origin, ladder["grid_size_m"], destination)
    stems = detect_stems(normalized, **_stem_config(config["dbh"]))
    _write_tree_table(stems_to_rows(stems), destination / "trees.csv")
    summary = {"n_points": len(points), "n_stems": len(stems)}
    (destination / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def _write_tree_table(rows: list[dict[str, float | int]], path: Path) -> None:
    """Write detected trees in a simple tabular format."""
    fields = ["x", "y", "dbh", "fit_residual", "n_points"]
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _stem_config(config: dict) -> dict:
    return {
        "slice_min": config["slice_min_m"],
        "slice_max": config["slice_max_m"],
        "radius": config["cluster_radius_m"],
        "min_points": config["min_points"],
        "min_dbh": config["min_radius_m"] * 2,
        "max_dbh": config["max_radius_m"] * 2,
        "max_residual": config["max_fit_residual_m"],
    }
