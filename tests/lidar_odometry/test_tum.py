"""Tests for odometry trajectory export."""

import numpy as np

from canopy.io.tum import write_tum


def test_write_tum_outputs_timestamp_and_pose(tmp_path) -> None:
    """A pose is exported as the eight standard TUM fields."""
    pose = np.eye(4)
    pose[0, 3] = 2.5
    path = tmp_path / "trajectory.tum"

    write_tum([(1_000_000_000, pose)], path)

    values = path.read_text().split()
    assert len(values) == 8
    assert values[:4] == ["1", "2.5", "0", "0"]
