"""Forest-analytics pipeline shared by ``canopy-analyze`` and the synthetic demo.

ground (CSF) -> height-normalise -> stems + DBH -> remove stem points ->
density bands and ladder-fuel proxy. ``analyse_points`` returns everything in
memory; ``analyze_cloud`` also writes the result files.
"""

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from canopy.config import section
from canopy.io import load_points

from .density import DensityGrid, density_grid
from .ground import GroundModel, normalize_heights
from .ladder_fuel import LadderFuel, ladder_fuel, save_ladder_report
from .stems import Stem, detect_stems, remove_stem_points, stems_to_rows

TREE_FIELDS = ["x", "y", "dbh", "fit_residual", "n_points", "arc_deg", "lean_deg"]


@dataclass(frozen=True)
class Analysis:
    """All analytics outputs for one point cloud."""

    ground: GroundModel
    is_ground: np.ndarray
    normalized: np.ndarray
    stems: list[Stem]
    density: DensityGrid
    ladder: LadderFuel


def analyse_points(points: np.ndarray) -> Analysis:
    """Run the full analytics chain on an (N, 3) cloud in map coordinates."""
    model, normalized, is_ground = normalize_heights(points)
    stems = detect_stems(normalized)
    vegetation = remove_stem_points(normalized[~is_ground], stems)
    ladder = ladder_fuel(vegetation if len(vegetation) else normalized)
    return Analysis(model, is_ground, normalized, stems, density_grid(normalized), ladder)


def analyze_cloud(cloud_path: str | Path, out_dir: str | Path) -> dict:
    """Analyse a point-cloud file and write the results to ``out_dir``."""
    points = load_points(cloud_path)
    result = analyse_points(points)
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    np.save(destination / "normalised_cloud.npy", result.normalized)
    np.save(destination / "ground_mask.npy", result.is_ground)
    np.save(destination / "dtm.npy", result.ground.elevations)
    _write_density(result.density, destination / "density.csv")
    save_ladder_report(result.ladder, destination)
    _write_tree_table(stems_to_rows(result.stems), destination / "trees.csv")
    summary = _summary(points, result)
    (destination / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def _summary(points: np.ndarray, result: Analysis) -> dict:
    dbh = np.array([stem.dbh for stem in result.stems])
    index = result.ladder.ladder_fuel_index
    return {
        "n_points": int(len(points)),
        "ground_method": section("ground")["method"],
        "ground_fraction": float(result.is_ground.mean()),
        "n_stems": len(result.stems),
        "mean_dbh_m": float(dbh.mean()) if len(dbh) else None,
        "ladder_cells": int(index.size),
        "ladder_mean_index": float(index.mean()),
        "ladder_cells_above_0_5": int((index > 0.5).sum()),
    }


def _write_density(density: DensityGrid, path: Path) -> None:
    """One row per cell: centre coordinates and the occupancy fraction of each band."""
    names = [f"band_{low:g}_{high:g}m" for low, high in density.bands]
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["x", "y", *names])
        for (i, j), _ in np.ndenumerate(density.occupancy[:, :, 0]):
            x = density.origin[0] + (i + 0.5) * density.resolution
            y = density.origin[1] + (j + 0.5) * density.resolution
            writer.writerow([f"{x:.2f}", f"{y:.2f}",
                             *(f"{value:.4f}" for value in density.occupancy[i, j])])


def _write_tree_table(rows: list[dict[str, float | int]], path: Path) -> None:
    """Write detected trees in a simple tabular format."""
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=TREE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
