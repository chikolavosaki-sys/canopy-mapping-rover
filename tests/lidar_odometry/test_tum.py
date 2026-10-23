"""Tests for odometry trajectory export."""

import numpy as np

from canopy.io import read_tum
from canopy.io.tum import write_tum


def test_write_tum_outputs_timestamp_and_pose(tmp_path) -> None:
    """A pose is exported as the eight standard TUM fields."""
    pose = np.eye(4)
    pose[0, 3] = 2.5
    path = tmp_path / "trajectory.tum"

    write_tum([(1_000_000_000, pose)], path)

    values = path.read_text().split()
    assert len(values) == 8
    np.testing.assert_allclose([float(value) for value in values[:4]], [1.0, 2.5, 0.0, 0.0])


def test_real_timestamps_keep_sub_second_precision(tmp_path) -> None:
    """Bag-style stamps 0.2 s apart stay distinct and round-trip with rotation."""
    pose = np.eye(4)
    pose[:2, :2] = [[0.0, -1.0], [1.0, 0.0]]
    stamps = [1_552_159_900_123_456_789, 1_552_159_900_323_456_789]
    path = tmp_path / "trajectory.tum"

    write_tum([(stamp, pose) for stamp in stamps], path)
    loaded = read_tum(path)

    assert path.read_text().split()[0] == "1552159900.123456789"
    assert abs((loaded[1][0] - loaded[0][0]) - 0.2) < 1e-6
    np.testing.assert_allclose(loaded[1][1], pose, atol=1e-9)
