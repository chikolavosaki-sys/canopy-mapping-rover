"""Command-line entry point for LiDAR odometry."""

import argparse
from pathlib import Path

import numpy as np

from canopy.io import save_points
from canopy.io.bag_reader import iter_pointclouds
from canopy.io.tum import write_tum

from .kiss_icp_runner import run_kiss_icp
from .register import register_scans


def main() -> None:
    """Run KISS-ICP on a directory of NPY frames."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--bag", type=Path, help="ROS1/ROS2 bag containing PointCloud2 frames")
    parser.add_argument("--topic", help="PointCloud2 topic for --bag")
    parser.add_argument("--synthetic", type=int, help="Reserved synthetic seed")
    parser.add_argument("--frames", type=Path, help="Directory containing ordered NPY scans")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.bag:
        if not args.topic:
            parser.error("--topic is required with --bag")
        frames = [frame for _, frame in iter_pointclouds(args.bag, args.topic)]
    elif args.topic:
        parser.error("--topic requires --bag")
    else:
        frames = []
    if args.synthetic is not None:
        raise NotImplementedError("synthetic traversal generation is owned by Phase 1 tests")
    if args.frames:
        frames = [np.load(path) for path in sorted(args.frames.glob("*.npy"))]
    elif not args.bag and args.synthetic is None:
        parser.error("provide --frames, --bag, or --synthetic")
    if args.synthetic is not None:
        raise NotImplementedError("synthetic traversal generation is reserved for the demo phase")
    if not frames:
        raise ValueError("no point-cloud frames were found")
    poses = run_kiss_icp(frames)
    output = args.out
    output.mkdir(parents=True, exist_ok=True)
    np.save(output / "poses.npy", np.stack(poses))
    write_tum(
        [(index * 1_000_000_000, pose) for index, pose in enumerate(poses)],
        output / "trajectory.tum",
    )
    save_points(register_scans(frames, poses), output / "map.npy")
