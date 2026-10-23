"""Optional KISS-ICP integration test."""

import numpy as np
import pytest

from canopy.lidar_odometry.kiss_icp_runner import run_kiss_icp


def test_kiss_icp_optional_dependency_or_pose_output() -> None:
    """The wrapper either reports its optional dependency or returns poses."""
    pytest.importorskip("kiss_icp")
    frame = np.random.default_rng(0).uniform(-5, 5, size=(200, 3))
    poses = run_kiss_icp([frame, frame])

    assert len(poses) == 2
    assert all(pose.shape == (4, 4) for pose in poses)
