"""Run the no-download synthetic end-to-end demonstration.

Chain: simulated drive -> KISS-ICP odometry -> one registered map -> forest
analytics -> evaluation against the simulator's exact ground truth. The same
analytics also run on two references, so losses can be traced:

- the same scans registered with the *exact* poses (isolates odometry error),
- the forest's perfect point cloud (upper bound for the analytics).
"""

import argparse
import json
from pathlib import Path

import numpy as np

from canopy.config import load_config
from canopy.evaluation.ladder_eval import evaluate_ladder
from canopy.evaluation.nav_eval import evaluate_navigation, summarise
from canopy.evaluation.odometry_eval import (
    absolute_position_error,
    final_drift_percent,
    relative_position_error,
    relative_to_first,
)
from canopy.evaluation.tree_eval import evaluate_trees
from canopy.forest_analytics.ground import normalize_heights
from canopy.forest_analytics.ladder_fuel import ladder_fuel_index, save_ladder_report
from canopy.forest_analytics.stems import detect_stems, stems_to_rows
from canopy.lidar_odometry import register_scans, run_kiss_icp, transform_points
from canopy.simulation.lidar import simulate_traversal
from canopy.simulation.synthetic_forest import Forest, make_forest, traversal_poses

Summary = dict[str, float | int]
OUTCOMES = Path(__file__).resolve().parents[1] / "docs" / "OUTCOMES.md"
MARKERS = ("<!-- demo-results:start -->", "<!-- demo-results:end -->")


def run_demo(seed: int, out_dir: Path) -> Summary:
    """Run odometry, mapping, analytics, and navigation; write the report files."""
    config = load_config()
    demo = config["demo"]
    out_dir.mkdir(parents=True, exist_ok=True)
    forest = make_forest(seed, demo["plot_size_m"], demo["tree_count"], demo["points_per_tree"])
    world_map, exact_map, summary = map_with_odometry(forest)
    map_metrics, map_trees = analyse(world_map, forest, config, out_dir)
    exact_metrics, _ = analyse(exact_map, forest, config, None)
    cloud_metrics, _ = analyse(forest.points, forest, config, None)
    results = {"map": map_metrics, "exact": exact_metrics, "cloud": cloud_metrics}
    for prefix, metrics in results.items():
        summary.update({f"{prefix}_{key}": value for key, value in metrics.items()})
    nav = config["navigation"]["eval"]
    first = nav["reported_seed_offset"] + seed
    seeds = range(first, first + nav["seeds_per_density"])
    overall = summarise(evaluate_navigation(seeds, out_dir=out_dir / "navigation"))[-1]
    summary["navigation_runs"] = overall["runs"]
    summary["navigation_success"] = overall["success_rate"]
    summary["navigation_collisions"] = overall["collisions"]
    summary["navigation_timeouts"] = overall["timeouts"]
    summary["navigation_path_ratio"] = overall["mean_path_ratio"]
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out_dir / "trees.json").write_text(json.dumps(map_trees, indent=2) + "\n")
    _write_report(summary, seed, out_dir / "report.md")
    return summary


def map_with_odometry(forest: Forest) -> tuple[np.ndarray, np.ndarray, Summary]:
    """Drive through the forest; return the KISS-ICP map, the exact-pose map, and metrics.

    KISS-ICP's map starts at the first scan. We place it in world coordinates
    with the known start pose, as a real rover would with a GPS fix at the start.
    """
    sequence = simulate_traversal(forest, traversal_poses(forest), sensor_frame=True)
    truth = relative_to_first([pose for pose, _ in sequence])
    scans = [scan for _, scan in sequence]
    estimated = run_kiss_icp(scans)
    world_map = transform_points(register_scans(scans, estimated), sequence[0][0])
    exact_map = transform_points(register_scans(scans, truth), sequence[0][0])
    summary: Summary = {
        "odometry_frames": len(scans),
        "odometry_path_m": float(
            np.sum(np.linalg.norm(np.diff([pose[:3, 3] for pose in truth], axis=0), axis=1))
        ),
        "odometry_ate_rmse_m": absolute_position_error(estimated, truth),
        "odometry_rpe_rmse_m": relative_position_error(estimated, truth),
        "odometry_drift_percent": final_drift_percent(estimated, truth),
        "map_points": len(world_map),
    }
    return world_map, exact_map, summary


def analyse(
    points: np.ndarray, forest: Forest, config: dict, out_dir: Path | None
) -> tuple[Summary, list[dict[str, float | int]]]:
    """Run ground removal, ladder fuel, and stem detection, then score them."""
    demo = config["demo"]
    _, normalized = normalize_heights(points)
    score, origin = ladder_fuel_index(normalized)
    resolution = config["ladder_fuel"]["grid_size_m"]
    if out_dir is not None:
        save_ladder_report(score, origin, resolution, out_dir)
    stems = detect_stems(
        normalized, radius=demo["stem_cluster_radius_m"], min_points=demo["stem_min_points"]
    )
    detected = stems_to_rows(stems)
    trees = evaluate_trees(detected, forest.trees)
    ladder = evaluate_ladder(score, shrub_cells(forest, score.shape, origin, resolution))
    metrics: Summary = {
        "trees_detected": len(detected),
        "tree_recall": trees.recall,
        "tree_precision": trees.precision,
        "dbh_rmse_m": trees.dbh_rmse,
        "dbh_bias_m": trees.dbh_bias,
        "ladder_spearman": ladder["spearman"],
        "ladder_auc": ladder["auc"],
    }
    return metrics, detected


def shrub_cells(
    forest: Forest, shape: tuple[int, int], origin: tuple[float, float], resolution: float
) -> np.ndarray:
    """Mark every grid cell that a shrub's footprint overlaps."""
    labels = np.zeros(shape, dtype=bool)
    for shrub in forest.shrubs:
        low = np.floor((np.array(shrub.minimum[:2]) - origin) / resolution).astype(int)
        high = np.floor((np.array(shrub.maximum[:2]) - origin) / resolution).astype(int)
        low, high = np.clip(low, 0, np.array(shape) - 1), np.clip(high, -1, np.array(shape) - 1)
        labels[low[0] : high[0] + 1, low[1] : high[1] + 1] = True
    return labels


def _write_report(summary: Summary, seed: int, path: Path) -> None:
    """Write a Markdown report with map-vs-upper-bound columns."""
    rows = [
        ("Trees detected", "trees_detected"),
        ("Tree recall", "tree_recall"),
        ("Tree precision", "tree_precision"),
        ("DBH RMSE (m)", "dbh_rmse_m"),
        ("DBH bias (m)", "dbh_bias_m"),
        ("Ladder Spearman vs shrub cells", "ladder_spearman"),
        ("Ladder AUC vs shrub cells", "ladder_auc"),
    ]
    lines = [
        f"# Synthetic demo results (seed {seed})",
        "",
        "Generated by `python scripts/run_all.py`. Synthetic data only; see",
        "`docs/OUTCOMES.md` for targets and honest limits.",
        "",
        "## Odometry (KISS-ICP vs exact simulated poses)",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Frames | {summary['odometry_frames']} |",
        f"| Path length (m) | {summary['odometry_path_m']:.2f} |",
        f"| ATE RMSE (m) | {summary['odometry_ate_rmse_m']:.4f} |",
        f"| RPE RMSE (m) | {summary['odometry_rpe_rmse_m']:.4f} |",
        f"| Final drift (% of path) | {summary['odometry_drift_percent']:.3f} |",
        "",
        "## Forest analytics",
        "",
        f"KISS-ICP map: {summary['map_points']} points from simulated scans registered with",
        "KISS-ICP. Exact-pose map: the same scans with the true poses (so the gap to the",
        "first column is odometry error). Perfect cloud: every forest point (upper bound).",
        "",
        "| Metric | KISS-ICP map | Exact-pose map | Perfect cloud |",
        "|---|---:|---:|---:|",
    ]
    columns = ("map", "exact", "cloud")
    lines += [
        f"| {label} | " + " | ".join(_fmt(summary[f"{c}_{key}"]) for c in columns) + " |"
        for label, key in rows
    ]
    lines += [
        "",
        "## Navigation (simulator)",
        "",
        "Per-density results: `navigation/navigation_summary.csv`.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Runs (seeds x forest densities) | {summary['navigation_runs']} |",
        f"| Success rate | {summary['navigation_success']:.3f} |",
        f"| Collisions | {summary['navigation_collisions']} |",
        f"| Time-outs | {summary['navigation_timeouts']} |",
        f"| Mean path ratio (driven / straight line) | {summary['navigation_path_ratio']:.3f} |",
        "",
        "![Ladder-fuel index from the scanned map](ladder_fuel.png)",
    ]
    path.write_text("\n".join(lines) + "\n")


def update_outcomes(summary: Summary, seed: int, path: Path = OUTCOMES) -> None:
    """Replace the marked results block in docs/OUTCOMES.md with this run's numbers."""
    text = path.read_text()
    start, end = (text.index(marker) for marker in MARKERS)
    rows = [
        ("Odometry final drift (% of path)", summary["odometry_drift_percent"], "< 2 %"),
        ("Odometry ATE RMSE (m)", summary["odometry_ate_rmse_m"], "-"),
        ("Tree recall, scanned map", summary["map_tree_recall"], ">= 0.90"),
        ("Tree recall, exact-pose map (no odometry error)", summary["exact_tree_recall"], "-"),
        ("Tree recall, perfect cloud (upper bound)", summary["cloud_tree_recall"], "-"),
        ("DBH RMSE (m), scanned map", summary["map_dbh_rmse_m"], "<= 0.03"),
        ("Ladder AUC vs shrub cells, scanned map", summary["map_ladder_auc"], ">= 0.75"),
        ("Navigation runs", summary["navigation_runs"], ">= 50"),
        ("Navigation success rate", summary["navigation_success"], ">= 0.90"),
        ("Navigation collisions", summary["navigation_collisions"], "0"),
    ]
    table = [f"Seed {seed}.", "", "| Metric | Value | Target |", "|---|---:|---:|"]
    table += [f"| {label} | {_fmt(value)} | {target} |" for label, value, target in rows]
    block = MARKERS[0] + "\n" + "\n".join(table) + "\n"
    path.write_text(text[:start] + block + text[end:])


def _fmt(value: float | int) -> str:
    """Counts as whole numbers, everything else to four decimals."""
    return str(value) if isinstance(value, int) else f"{value:.4f}"


def main() -> None:
    """Parse demo arguments and run the synthetic pipeline."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=Path("results/demo"))
    parser.add_argument(
        "--update-outcomes", action="store_true", help="rewrite the table in docs/OUTCOMES.md"
    )
    args = parser.parse_args()
    summary = run_demo(args.seed, args.out)
    if args.update_outcomes:
        update_outcomes(summary, args.seed)


if __name__ == "__main__":
    main()
