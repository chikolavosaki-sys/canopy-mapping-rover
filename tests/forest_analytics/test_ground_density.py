"""Tests for terrain normalization and occupancy density."""

import numpy as np

from canopy.forest_analytics.density import density_grid
from canopy.forest_analytics.ground import normalize_heights


def test_ground_normalization_removes_sloped_surface() -> None:
    """A point above a local synthetic ground cell has the expected height."""
    ground = np.array([[x, y, 0.1 * x] for x in range(3) for y in range(3)])
    _, normalized = normalize_heights(ground, resolution=1.0, quantile=0.1)

    np.testing.assert_allclose(normalized[:, 2], 0.0)


def test_density_uses_unique_vertical_voxels() -> None:
    """Repeated returns in one voxel do not inflate occupancy."""
    points = np.array([[0.1, 0.1, 1.1], [0.1, 0.1, 1.11], [0.1, 0.1, 1.25]])

    result = density_grid(points, ((1.0, 2.0),), resolution=1.0, voxel_size=0.1)

    assert result.occupancy[0, 0, 0] == 2


def test_ransac_plane_ignores_points_above_the_ground() -> None:
    """A trunk standing on a tilted plane does not pull the fitted plane up."""
    from canopy.forest_analytics.ground import fit_plane_ransac, lowest_per_cell

    x, y = (axis.ravel() for axis in np.meshgrid(np.arange(10.0), np.arange(10.0)))
    ground = np.column_stack((x, y, 0.2 * x + 0.1 * y + 1.0))
    trunk = np.column_stack((np.full(20, 4.5), np.full(20, 4.5), np.linspace(2, 6, 20)))
    points = np.vstack((ground, trunk))

    lowest = points[lowest_per_cell(points, 1.0)]
    plane, inliers = fit_plane_ransac(lowest, distance=0.05, iterations=50)

    np.testing.assert_allclose(plane, [0.2, 0.1, 1.0], atol=1e-9)
    # In the trunk's cell the trunk base (z 2.0) is lower than the ground (z 2.2), so it is
    # that cell's candidate; RANSAC must reject exactly that one point.
    assert inliers.sum() == 99
    assert not inliers[np.flatnonzero(np.isclose(lowest[:, 0], 4.5))].any()
