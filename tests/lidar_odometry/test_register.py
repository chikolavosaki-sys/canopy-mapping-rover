"""Tests for registered point-cloud maps."""

import numpy as np

from canopy.lidar_odometry.register import register_scans, transform_points


def test_transform_and_register_scans() -> None:
    """A pose inverse-aligns a translated scan into the world map."""
    scan = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    pose = np.eye(4)
    pose[0, 3] = 2.0

    transformed = transform_points(scan, pose)
    registered = register_scans([scan, transformed], [np.eye(4), np.linalg.inv(pose)], 0.01)

    np.testing.assert_allclose(np.sort(registered, axis=0), np.sort(scan, axis=0))
