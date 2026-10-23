"""KISS-ICP integration with an explicit optional-dependency boundary.

KISS-ICP estimates how the LiDAR moved between scans by aligning each new
scan to a small local map built from the previous ones (point-to-point ICP).
It needs no IMU. We call its ``KissICP`` class directly, one frame at a time,
and read the estimated pose from ``last_pose`` after each frame.
"""

from collections.abc import Sequence

import numpy as np

from canopy.config import section

_ODOM = section("odometry")


def run_kiss_icp(
    frames: Sequence[np.ndarray], voxel_size: float = _ODOM["voxel_size_m"]
) -> list[np.ndarray]:
    """Estimate one 4x4 world pose per LiDAR frame; the first pose is identity.

    KISS-ICP is imported only when this function is called, so the rest of
    the project works without the optional ``odometry`` extra.
    """
    if not frames:
        return []
    try:
        from kiss_icp.kiss_icp import KissICP
    except ImportError as error:
        raise ImportError(
            "KISS-ICP is required for run_kiss_icp; install with "
            '`pip install -e ".[odometry]"`'
        ) from error
    estimator = KissICP(_kiss_config(voxel_size))
    no_timestamps = np.array([])  # tells KISS-ICP there is nothing to deskew
    poses = []
    for frame in frames:
        estimator.register_frame(_validate_frame(frame), no_timestamps)
        poses.append(np.asarray(estimator.last_pose, dtype=np.float64).copy())
    return poses


def _kiss_config(voxel_size: float) -> object:
    """Build KISS-ICP's own config object from our YAML settings."""
    from kiss_icp.config import load_config

    config = load_config(None)
    config.data.min_range = _ODOM["min_range_m"]
    config.data.max_range = _ODOM["max_range_m"]
    config.data.deskew = _ODOM["deskew"]
    config.mapping.voxel_size = voxel_size
    config.mapping.max_points_per_voxel = _ODOM["max_points_per_voxel"]
    return config


def _validate_frame(frame: np.ndarray) -> np.ndarray:
    values = np.asarray(frame, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("each LiDAR frame must have shape (N, 3)")
    return values[np.all(np.isfinite(values), axis=1)]
