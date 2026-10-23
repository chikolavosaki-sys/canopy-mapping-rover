"""KISS-ICP integration with an explicit optional-dependency boundary."""

from collections.abc import Sequence

import numpy as np

from canopy.config import section


def run_kiss_icp(
    frames: Sequence[np.ndarray], voxel_size: float = section("odometry")["voxel_size_m"]
) -> list[np.ndarray]:
    """Estimate one world pose per LiDAR frame with KISS-ICP.

    KISS-ICP is imported only when this function is called. This keeps
    synthetic tests and the rest of the project usable without installing the
    optional odometry extra.
    """
    if not frames:
        return []
    try:
        from kiss_icp.pipeline import OdometryPipeline
    except ImportError as error:
        raise ImportError(
            "KISS-ICP is required for run_kiss_icp; install with "
            '`pip install -e ".[odometry]"`'
        ) from error
    estimator = _make_pipeline(OdometryPipeline, voxel_size)
    poses = []
    for frame in frames:
        scan = _validate_frame(frame)
        returned_pose = estimator.register_frame(scan)
        pose = returned_pose if returned_pose is not None else estimator.last_pose
        poses.append(np.asarray(pose, dtype=np.float64).copy())
    return poses


def _validate_frame(frame: np.ndarray) -> np.ndarray:
    values = np.asarray(frame, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("each LiDAR frame must have shape (N, 3)")
    return values


def _make_pipeline(pipeline_type: type, voxel_size: float) -> object:
    """Construct the current KISS-ICP pipeline with compatible defaults."""
    try:
        return pipeline_type(voxel_size=voxel_size)
    except TypeError:
        return pipeline_type()
