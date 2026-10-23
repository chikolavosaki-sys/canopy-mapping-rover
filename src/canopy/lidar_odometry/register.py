"""Point-cloud registration helpers."""

from collections.abc import Sequence

import numpy as np

from canopy.config import load_config
from canopy.io import voxel_downsample


def transform_points(points: np.ndarray, pose: np.ndarray) -> np.ndarray:
    """Transform an ``(N, 3)`` cloud by a homogeneous pose."""
    values = np.asarray(points, dtype=np.float64)
    matrix = np.asarray(pose, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 3 or matrix.shape != (4, 4):
        raise ValueError("points must be (N, 3) and pose must be (4, 4)")
    return (matrix @ np.column_stack((values, np.ones(len(values)))).T).T[:, :3]


def register_scans(
    scans: Sequence[np.ndarray],
    poses: Sequence[np.ndarray],
    voxel_size: float = load_config()["map_voxel_size_m"],
) -> np.ndarray:
    """Transform scans into the first world frame and return one downsampled map."""
    if len(scans) != len(poses):
        raise ValueError("scans and poses must have equal lengths")
    if not scans:
        return np.empty((0, 3), dtype=np.float64)
    merged = np.vstack([transform_points(scan, pose) for scan, pose in zip(scans, poses)])
    return voxel_downsample(merged, voxel_size)
