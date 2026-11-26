"""Run the no-download synthetic end-to-end demonstration.

Chain: simulated drive -> KISS-ICP odometry -> one registered map -> forest
analytics -> evaluation against the simulator's exact ground truth. The same
analytics also run on two references, so losses can be traced:

- the same scans registered with the *exact* poses (isolates odometry error),
- the forest's perfect point cloud (upper bound for the analytics).
"""

import argparse
import json
from dataclasses import dataclass
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
from canopy.forest_analytics.ground import normalize_heights, resolve_method
from canopy.forest_analytics.ladder_fuel import LadderFuel, save_ladder_report
from canopy.forest_analytics.pipeline import analyse_points, write_tree_table
from canopy.forest_analytics.stems import stems_to_rows
from canopy.lidar_odometry import register_scans, run_kiss_icp, transform_points
from canopy.simulation.lidar import (
    OdometryMode,
    mapping_frames,
    scan_with_labels,
    simulate_traversal,
)
from canopy.simulation.synthetic_forest import Forest, make_demo_forest, traversal_poses

Summary = dict[str, float | int | str]
OUTCOMES = Path(__file__).resolve().parents[1] / "docs" / "OUTCOMES.md"
MARKERS = ("<!-- demo-results:start -->", "<!-- demo-results:end -->")


@dataclass(frozen=True)
class MappingRun:
    """Registered clouds and trajectories in simulator world coordinates."""

    cloud: np.ndarray
    exact_cloud: np.ndarray
    estimated: np.ndarray
    reference: np.ndarray
    metrics: Summary


def run_demo(
    seed: int, out_dir: Path, fast: bool = False, odometry_mode: OdometryMode = "ground-filtered"
) -> Summary:
    """Run odometry, mapping, analytics, and navigation; write the report files."""
    config = load_config()
    out_dir.mkdir(parents=True, exist_ok=True)
    forest = make_demo_forest(seed)
    mapping = map_with_odometry(forest, odometry_mode)
    summary = dict(mapping.metrics)
    summary["ground_method"] = resolve_method()
    map_metrics, map_trees, ladder = analyse(mapping.cloud, forest)
    exact_metrics, _, _ = analyse(mapping.exact_cloud, forest)
    cloud_metrics, _, _ = analyse(forest.points, forest)
    save_ladder_report(ladder, out_dir)
    save_survey_map(mapping, ladder, forest, map_trees, out_dir / "survey_map.png")
    write_tree_table(map_trees, out_dir / "trees.csv")
    np.save(out_dir / "map.npy", mapping.cloud)
    summary.update(ground_scores(forest))
    results = {"map": map_metrics, "exact": exact_metrics, "cloud": cloud_metrics}
    for prefix, metrics in results.items():
        summary.update({f"{prefix}_{key}": value for key, value in metrics.items()})
    nav = config["navigation"]["eval"]
    first = nav["reported_seed_offset"] + seed
    seeds = range(first, first + (2 if fast else nav["seeds_per_density"]))
    tree_counts = (10, 40) if fast else tuple(nav["tree_counts"])
    overall = summarise(
        evaluate_navigation(seeds, tree_counts=tree_counts, out_dir=out_dir / "navigation")
    )[-1]
    summary["navigation_seed_start"] = seeds.start
    summary["navigation_seed_end"] = seeds.stop - 1
    summary["navigation_runs"] = overall["runs"]
    summary["navigation_success"] = overall["success_rate"]
    summary["navigation_collisions"] = overall["collisions"]
    summary["navigation_timeouts"] = overall["timeouts"]
    summary["navigation_path_ratio"] = overall["mean_path_ratio"]
    clean = {key: None if isinstance(value, float) and not np.isfinite(value) else value
             for key, value in summary.items()}
    (out_dir / "summary.json").write_text(
        json.dumps(clean, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (out_dir / "trees.json").write_text(json.dumps(map_trees, indent=2) + "\n", encoding="utf-8")
    _write_report(summary, seed, out_dir / "report.md")
    return summary


def map_with_odometry(forest: Forest, mode: OdometryMode = "ground-filtered") -> MappingRun:
    """Drive through the forest and compare the KISS-ICP map with the exact-pose map.

    KISS-ICP's map starts at the first scan. We place it in world coordinates
    with the known start pose, as a real rover would with a GPS fix at the start.
    """
    sequence = simulate_traversal(forest, traversal_poses(forest), sensor_frame=True)
    truth = relative_to_first([pose for pose, _ in sequence])
    scans = [scan for _, scan in sequence]
    frames, used_mode = mapping_frames(scans, mode)
    estimated = run_kiss_icp(frames)
    start_pose = sequence[0][0]
    world_map = transform_points(register_scans(scans, estimated), start_pose)
    exact_map = transform_points(register_scans(scans, truth), start_pose)
    summary: Summary = {
        "odometry_mode": used_mode,
        "odometry_requested_mode": mode,
        "odometry_frames": len(scans),
        "odometry_path_m": float(
            np.sum(np.linalg.norm(np.diff([pose[:3, 3] for pose in truth], axis=0), axis=1))
        ),
        "odometry_ate_rmse_m": absolute_position_error(estimated, truth),
        "odometry_rpe_rmse_m": relative_position_error(estimated, truth),
        "odometry_drift_percent": final_drift_percent(estimated, truth),
        "map_points": len(world_map),
    }
    return MappingRun(
        world_map,
        exact_map,
        transform_points(np.asarray(estimated)[:, :3, 3], start_pose),
        np.asarray([pose[:3, 3] for pose, _ in sequence]),
        summary,
    )


def analyse(
    points: np.ndarray, forest: Forest,
) -> tuple[Summary, list[dict[str, float | int]], LadderFuel]:
    """Run the shared analytics pipeline on one cloud and score it against the truth."""
    result = analyse_points(points)
    detected = stems_to_rows(result.stems)
    trees = evaluate_trees(detected, forest.trees)
    index = result.ladder.ladder_fuel_index
    shrubs = shrub_cells(forest, index.shape, result.ladder.origin, result.ladder.resolution)
    ladder = evaluate_ladder(index, shrubs)
    metrics: Summary = {
        "trees_detected": len(detected),
        "tree_recall": trees.recall,
        "tree_precision": trees.precision,
        "dbh_rmse_m": trees.dbh_rmse,
        "dbh_bias_m": trees.dbh_bias,
        "ladder_spearman": ladder["spearman"],
        "ladder_auc": ladder["auc"],
    }
    return metrics, detected, result.ladder


def save_survey_map(
    mapping: MappingRun,
    ladder: LadderFuel,
    forest: Forest,
    trees: list[dict[str, float | int]],
    path: Path,
) -> None:
    """Plot the mapped vegetation, measured trees and path against simulator references."""
    import matplotlib.pyplot as plt

    nx, ny = ladder.ladder_fuel_index.shape
    x0, y0 = ladder.origin
    extent = (x0, x0 + nx * ladder.resolution, y0, y0 + ny * ladder.resolution)
    figure, axis = plt.subplots(figsize=(8, 7), layout="constrained")
    heatmap = axis.imshow(
        ladder.ladder_fuel_index.T, extent=extent, origin="lower", cmap="YlOrBr", vmin=0, vmax=1
    )
    figure.colorbar(heatmap, ax=axis, shrink=0.8, label="Ladder-fuel proxy (0 to 1)")
    axis.plot(*mapping.reference[:, :2].T, color="#30434d", lw=1.6, label="Exact simulator path")
    axis.plot(
        *mapping.estimated[:, :2].T, color="#1765ad", ls="--", lw=1.8, label="Estimated LiDAR path"
    )
    if forest.trees:
        axis.scatter(
            [tree.x for tree in forest.trees], [tree.y for tree in forest.trees],
            facecolors="none", edgecolors="#30434d", s=84, label="Reference trees",
        )
    if trees:
        axis.scatter(
            [tree["x"] for tree in trees], [tree["y"] for tree in trees],
            color="#1765ad", marker="+", s=60, label="Detected trees",
        )
    bounds = (0, forest.plot_size_m)
    axis.set(xlabel="X (m)", ylabel="Y (m)", xlim=bounds, ylim=bounds)
    axis.set_title("Simulated forest survey", loc="left", fontweight="bold")
    axis.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncols=2, frameon=False)
    figure.savefig(path, dpi=160)
    plt.close(figure)


def ground_scores(forest: Forest) -> Summary:
    """Ground precision/recall on the labelled scans of the demo drive (exact poses).

    Rock points are left out of the precision: CSF drapes over low boulders and
    calls them terrain, which is normal for ground filters (docs/OUTCOMES.md).
    """
    poses = traversal_poses(forest)
    scans = [scan_with_labels(forest, pose, seed=index) for index, pose in enumerate(poses)]
    points = np.vstack([scan[0] for scan in scans])
    labels = np.concatenate([scan[1] for scan in scans])
    _, _, is_ground = normalize_heights(points)
    truth = labels == "ground"
    hits = int((is_ground & truth).sum())
    return {
        "ground_precision": hits / max(int((is_ground & (labels != "rock")).sum()), 1),
        "ground_recall": hits / max(int(truth.sum()), 1),
    }


def shrub_cells(
    forest: Forest, shape: tuple[int, int], origin: tuple[float, float], resolution: float
) -> np.ndarray:
    """Mark every grid cell that a shrub's footprint overlaps."""
    labels = np.zeros(shape, dtype=bool)
    for shrub in forest.shrubs:
        low = np.floor((np.array(shrub.minimum[:2]) - origin) / resolution).astype(int)
        high = np.floor((np.array(shrub.maximum[:2]) - origin) / resolution).astype(int)
        low, high = np.maximum(low, 0), np.minimum(high, np.array(shape) - 1)
        if np.any(low > high):
            continue
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
        f"| Alignment returns | {summary['odometry_mode']} |",
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
        f"Ground classification ({summary['ground_method']}) on the labelled demo scans: "
        f"precision {summary['ground_precision']:.3f} (rocks excluded), "
        f"recall {summary['ground_recall']:.3f}.",
        "",
        "## Navigation (simulator)",
        "",
        "Per-density results: `navigation/navigation_summary.csv`.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Seed range | {summary['navigation_seed_start']}-{summary['navigation_seed_end']} |",
        f"| Runs (seeds x forest densities) | {summary['navigation_runs']} |",
        f"| Success rate | {summary['navigation_success']:.3f} |",
        f"| Collisions | {summary['navigation_collisions']} |",
        f"| Time-outs | {summary['navigation_timeouts']} |",
        f"| Mean path ratio (driven / straight line) | {summary['navigation_path_ratio']:.3f} |",
        "",
        "![Survey map with path and tree detections](survey_map.png)",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_outcomes(summary: Summary, seed: int, path: Path = OUTCOMES) -> None:
    """Replace the marked results block in docs/OUTCOMES.md with this run's numbers."""
    text = path.read_text(encoding="utf-8")
    start, end = (text.index(marker) for marker in MARKERS)
    rows = [
        ("Odometry final drift (% of path)", summary["odometry_drift_percent"], "< 2 %"),
        ("Odometry ATE RMSE (m)", summary["odometry_ate_rmse_m"], "-"),
        ("Tree recall, scanned map", summary["map_tree_recall"], ">= 0.90"),
        ("Tree recall, exact-pose map (no odometry error)", summary["exact_tree_recall"], "-"),
        ("Tree recall, perfect cloud (upper bound)", summary["cloud_tree_recall"], "-"),
        ("DBH RMSE (m), scanned map", summary["map_dbh_rmse_m"], "<= 0.03"),
        ("DBH RMSE (m), exact-pose map", summary["exact_dbh_rmse_m"], "<= 0.03"),
        ("Ground precision (rocks excluded) / recall",
         f"{summary['ground_precision']:.3f} / {summary['ground_recall']:.3f}", "-"),
        ("Ladder AUC vs shrub cells, scanned map", summary["map_ladder_auc"], ">= 0.75"),
        ("Navigation runs", summary["navigation_runs"], ">= 50"),
        ("Navigation success rate", summary["navigation_success"], ">= 0.90"),
        ("Navigation collisions", summary["navigation_collisions"], "0"),
        ("Navigation timeouts", summary["navigation_timeouts"], "-"),
    ]
    table = [
        f"Seed {seed}. Ground classification used {str(summary['ground_method']).upper()}.",
        f"Navigation seeds {summary['navigation_seed_start']}-{summary['navigation_seed_end']}.",
        "",
        "| Metric | Value | Target |",
        "|---|---:|---:|",
    ]
    table += [f"| {label} | {_fmt(value)} | {target} |" for label, value, target in rows]
    block = MARKERS[0] + "\n" + "\n".join(table) + "\n"
    path.write_text(text[:start] + block + text[end:], encoding="utf-8")


def _fmt(value: float | int | str) -> str:
    """Counts as whole numbers, missing values as n/a, everything else to four decimals."""
    if isinstance(value, (int, str)):
        return str(value)
    return "n/a" if np.isnan(value) else f"{value:.4f}"


def main() -> None:
    """Parse demo arguments and run the synthetic pipeline."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=Path("results/runs/demo"))
    parser.add_argument(
        "--odometry", choices=("ground-filtered", "all-returns"), default="ground-filtered",
        help="choose which simulated LiDAR returns are used to estimate motion",
    )
    parser.add_argument(
        "--fast", action="store_true", help="fast run for live demos (4 nav trials)"
    )
    parser.add_argument(
        "--update-outcomes", action="store_true", help="rewrite the table in docs/OUTCOMES.md"
    )
    args = parser.parse_args()
    if args.seed < 0:
        parser.error("--seed must be non-negative")
    if args.fast and args.update_outcomes:
        parser.error("--fast runs only 4 navigation trials; do not use it with --update-outcomes")
    print(f"Running the synthetic forest survey (seed {args.seed})...", flush=True)
    summary = run_demo(args.seed, args.out, fast=args.fast, odometry_mode=args.odometry)
    if args.update_outcomes:
        update_outcomes(summary, args.seed)
    print(f"Wrote the survey map, tree table, and metrics to {args.out.resolve()}")


if __name__ == "__main__":
    main()
