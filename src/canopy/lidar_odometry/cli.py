"""Command-line entry point for LiDAR odometry.

Examples::

    canopy-odometry --synthetic 0 --out results/odom-synthetic
    canopy-odometry --bag data/raw/treescope/WSF-19/input/cloud3.bag \\
        --topic /velodyne/cloud --out results/odom-wsf19
    canopy-odometry --frames scans_dir/ --out results/odom-frames
"""

import argparse
import json
from pathlib import Path

import numpy as np

from canopy.config import section
from canopy.evaluation.odometry_eval import (
    absolute_position_error,
    relative_position_error,
    relative_to_first,
    start_to_end_drift,
)
from canopy.io import save_points
from canopy.io.bag_reader import iter_pointclouds
from canopy.io.tum import write_tum

from .kiss_icp_runner import run_kiss_icp
from .register import register_scans


def main() -> None:
    """Run KISS-ICP on a bag, a folder of NPY scans, or a synthetic traversal."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--bag", type=Path, help="ROS1/ROS2 bag with PointCloud2 frames")
    source.add_argument("--frames", type=Path, help="Folder of ordered sensor-frame NPY scans")
    source.add_argument("--synthetic", type=int, metavar="SEED", help="Simulated forest seed")
    parser.add_argument("--topic", help="PointCloud2 topic (required with --bag)")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.bag and not args.topic:
        parser.error("--topic is required with --bag")
    stamps, frames, reference = _load_input(args)
    if not frames:
        parser.error("no point-cloud frames were found")
    summary = run_and_save(stamps, frames, args.out, reference)
    print(json.dumps(summary, indent=2))


def _load_input(args: argparse.Namespace) -> tuple[list[int], list[np.ndarray], list | None]:
    """Return nanosecond timestamps, sensor-frame scans, and exact poses if known."""
    if args.bag:
        pairs = list(iter_pointclouds(args.bag, args.topic))
        return [stamp for stamp, _ in pairs], [frame for _, frame in pairs], None
    if args.frames:
        frames = [np.load(path) for path in sorted(args.frames.glob("*.npy"))]
        return _even_stamps(len(frames)), frames, None
    poses, frames = synthetic_sequence(args.synthetic)
    return _even_stamps(len(frames)), frames, poses


def synthetic_sequence(seed: int) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Simulate a traversal and return exact world poses and sensor-frame scans."""
    from canopy.simulation.synthetic_forest import (
        make_forest,
        simulate_traversal,
        traversal_poses,
    )

    forest = make_forest(seed)
    sequence = simulate_traversal(forest, traversal_poses(forest.plot_size_m), sensor_frame=True)
    return [pose for pose, _ in sequence], [scan for _, scan in sequence]


def run_and_save(
    stamps: list[int],
    frames: list[np.ndarray],
    out: Path,
    reference: list[np.ndarray] | None = None,
) -> dict[str, float | int | str]:
    """Run KISS-ICP, write trajectory and map files, and return a summary."""
    poses = run_kiss_icp(frames)
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "poses.npy", np.stack(poses))
    write_tum(list(zip(stamps, poses)), out / "trajectory.tum")
    save_points(register_scans(frames, poses), out / "map.npy")
    positions = np.array([pose[:3, 3] for pose in poses])
    summary: dict[str, float | int | str] = {
        "frames": len(poses),
        "path_length_m": float(np.sum(np.linalg.norm(np.diff(positions, axis=0), axis=1))),
        "start_to_end_m": start_to_end_drift(poses),
        "reference": "none",
    }
    if reference is not None:
        truth = relative_to_first(reference)
        write_tum(list(zip(stamps, truth)), out / "reference.tum")
        summary["reference"] = "exact synthetic poses"
        summary["ate_rmse_m"] = absolute_position_error(poses, truth)
        summary["rpe_rmse_m"] = relative_position_error(poses, truth)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def _even_stamps(count: int) -> list[int]:
    """Nanosecond timestamps at the configured frame period, for inputs without them."""
    period_ns = int(section("odometry")["frame_period_s"] * 1e9)
    return [index * period_ns for index in range(count)]
