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
