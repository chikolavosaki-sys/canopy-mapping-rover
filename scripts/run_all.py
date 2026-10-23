"""Run the no-download synthetic end-to-end demonstration."""

import argparse
import json
from pathlib import Path

import numpy as np

from canopy.evaluation.ladder_eval import evaluate_ladder
from canopy.evaluation.nav_eval import evaluate_navigation
from canopy.evaluation.odometry_eval import absolute_position_error, relative_position_error
from canopy.evaluation.tree_eval import evaluate_trees
from canopy.forest_analytics.ground import normalize_heights
from canopy.forest_analytics.ladder_fuel import ladder_fuel_index, save_ladder_report
from canopy.forest_analytics.stems import detect_stems, stems_to_rows
from canopy.simulation.synthetic_forest import make_forest


def run_demo(seed: int, out_dir: Path) -> dict[str, float | int]:
    """Generate synthetic data, run analytics and navigation, and write a report."""
    forest = make_forest(seed, plot_size_m=20.0, n_trees=6, points_per_tree=1000)
    _, normalized = normalize_heights(forest.points)
    score, origin = ladder_fuel_index(normalized)
    save_ladder_report(score, origin, 1.0, out_dir)
    detected = stems_to_rows(detect_stems(normalized, radius=0.45, min_points=10))
    tree_metrics = evaluate_trees(detected, forest.trees)
    shrub_cells = _shrub_cells(forest, score.shape, origin)
    ladder_metrics = evaluate_ladder(score, shrub_cells)
    navigation = evaluate_navigation(range(seed, seed + 5), 20.0, 6, out_dir / "navigation")
    nav_success = sum(result.reached_goal for result in navigation) / len(navigation)
    poses = [_pose(float(index), 0.0) for index in range(5)]
    estimated = [_pose(float(index) + 0.01 * index, 0.0) for index in range(5)]
    summary = {
        "tree_recall": tree_metrics.recall,
        "tree_precision": tree_metrics.precision,
        "dbh_rmse_m": tree_metrics.dbh_rmse,
        "ladder_spearman": ladder_metrics["spearman"],
        "ladder_auc": ladder_metrics["auc"],
        "navigation_success": nav_success,
        "synthetic_ate_rmse_m": absolute_position_error(estimated, poses),
        "synthetic_rpe_rmse_m": relative_position_error(estimated, poses),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    _write_report(summary, out_dir / "report.md")
    (out_dir / "trees.json").write_text(json.dumps(detected, indent=2) + "\n")
    return summary


def _pose(x: float, y: float) -> np.ndarray:
    pose = np.eye(4)
    pose[:2, 3] = (x, y)
    return pose


def _shrub_cells(
    forest, shape: tuple[int, int], origin: tuple[float, float]
) -> np.ndarray:
    cells = np.floor(
        np.array([[shrub.minimum[0], shrub.minimum[1]] for shrub in forest.shrubs]) - origin
    ).astype(int)
    labels = np.zeros(shape, dtype=bool)
    for x, y in cells:
        if 0 <= x < shape[0] and 0 <= y < shape[1]:
            labels[x, y] = True
    return labels


def _write_report(summary: dict[str, float | int], path: Path) -> None:
    lines = ["# Synthetic demo results", "", "| Metric | Value |", "|---|---:|"]
    lines.extend(f"| {key} | {value:.4f} |" for key, value in summary.items())
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Parse demo arguments and run the synthetic pipeline."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=Path("results/demo"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    run_demo(args.seed, args.out)


if __name__ == "__main__":
    main()
