"""Command-line entry point for LiDAR odometry."""

import argparse
from pathlib import Path

import numpy as np

from canopy.io import save_points
from canopy.io.tum import write_tum

from .kiss_icp_runner import run_kiss_icp
from .register import register_scans


def main() -> None:
    """Run KISS-ICP on a directory of NPY frames."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--bag", type=Path, help="ROS1/ROS2 bag; adapter wiring is pending")
    parser.add_argument("--topic", help="PointCloud2 topic for --bag")
    parser.add_argument("--synthetic", type=int, help="Reserved synthetic seed")
    parser.add_argument("--frames", type=Path, help="Directory containing ordered NPY scans")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.bag:
        raise NotImplementedError("bag CLI wiring is reserved for the real-data adapter phase")
    if args.synthetic is not None:
        raise NotImplementedError("synthetic traversal generation is owned by Phase 1 tests")
    if not args.frames:
        parser.error("provide --frames, --bag, or --synthetic")
    frames = [np.load(path) for path in sorted(args.frames.glob("*.npy"))]
    poses = run_kiss_icp(frames)
    output = args.out
    output.mkdir(parents=True, exist_ok=True)
    np.save(output / "poses.npy", np.stack(poses))
    write_tum(
        [(index * 1_000_000_000, pose) for index, pose in enumerate(poses)],
        output / "trajectory.tum",
    )
    save_points(register_scans(frames, poses), output / "map.npy")
