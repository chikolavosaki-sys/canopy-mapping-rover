"""Tests for dependency-light point-cloud helpers."""

import numpy as np

from canopy.io import crop_box, crop_radius, load_points, save_points, voxel_downsample


def test_npy_round_trip_and_crops(tmp_path) -> None:
    """NPY I/O and geometric filters preserve expected coordinates."""
    points = np.array([[0.0, 0.0, 0.0], [0.04, 0.04, 0.04], [2.0, 0.0, 0.0]])
    path = tmp_path / "points.npy"
    save_points(points, path)

    np.testing.assert_allclose(load_points(path), points)
    np.testing.assert_allclose(voxel_downsample(points, 0.1), points[[0, 2]])
    np.testing.assert_allclose(crop_box(points, [-1, -1, -1], [1, 1, 1]), points[:2])
    np.testing.assert_allclose(crop_radius(points, [0, 0, 0], 0.1), points[:2])
