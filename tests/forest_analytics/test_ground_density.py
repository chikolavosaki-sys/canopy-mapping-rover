"""Tests for ground classification, the DTM, height normalisation, and density."""

import numpy as np
import pytest

from canopy.forest_analytics.density import density_grid
from canopy.forest_analytics.ground import (
    fit_dtm,
    fit_plane_ransac,
    lowest_per_cell,
    normalize_heights,
)
from canopy.simulation.lidar import scan_with_labels
from canopy.simulation.synthetic_forest import make_forest, traversal_poses


@pytest.fixture(scope="module")
def steep_scanned_map() -> tuple[np.ndarray, np.ndarray]:
    """A labelled map from a short drive through a 15-degree synthetic forest."""
    forest = make_forest(seed=0, plot_size_m=15.0, n_trees=5, points_per_tree=500, slope_deg=15.0)
    poses = traversal_poses(forest)
    scans = [scan_with_labels(forest, pose, seed=i) for i, pose in enumerate(poses)]
    return np.vstack([s[0] for s in scans]), np.concatenate([s[1] for s in scans])


@pytest.mark.parametrize("method", ["csf", "ransac"])
def test_ground_classification_matches_labels_on_a_15_degree_slope(steep_scanned_map, method):
    """Both methods find >= 95 % of ground; >= 95 % of what they call ground really is.

    Rock points are left out of the precision: CSF's cloth drapes over low
    boulders and calls them terrain, which is normal for ground filters and
    hardly affects the 1.2-1.4 m DBH slice (see docs/OUTCOMES.md limits).
    """
    points, labels = steep_scanned_map
    _, _, is_ground = normalize_heights(points, method=method)
    truth, not_rock = labels == "ground", labels != "rock"
    precision = (is_ground & truth).sum() / (is_ground & not_rock).sum()
    recall = (is_ground & truth).sum() / truth.sum()

    assert precision >= 0.95, f"{method} precision {precision:.3f}"
    assert recall >= 0.95, f"{method} recall {recall:.3f}"


def test_heights_are_measured_from_the_sloped_ground() -> None:
    """On a 0.25 slope, a point 1.3 m above the ground gets height 1.3 (interpolated DTM)."""
    x, y = (axis.ravel() for axis in np.meshgrid(np.arange(0, 10, 0.25), np.arange(0, 10, 0.25)))
    ground = np.column_stack((x, y, 0.25 * x))
    trunk = np.array([[4.6, 5.2, 0.25 * 4.6 + 1.3]])

    _, normalized, is_ground = normalize_heights(np.vstack((ground, trunk)), method="ransac")

    np.testing.assert_allclose(normalized[:-1, 2], 0.0, atol=0.02)
    assert abs(normalized[-1, 2] - 1.3) < 0.02
    assert not is_ground[-1]


def test_dtm_fills_empty_cells_from_the_nearest_ground() -> None:
    """A cell with no ground points copies its neighbour, not the plot median."""
    points = np.array([[0.5, 0.5, 1.0], [1.5, 0.5, 1.0], [5.5, 0.5, 9.0], [2.5, 0.5, 5.0]])
    is_ground = np.array([True, True, True, False])

    model = fit_dtm(points, is_ground, resolution=1.0)

    assert model.elevations[2, 0] == 1.0  # empty cell next to the low cells
    assert model.elevations[5, 0] == 9.0


def test_ransac_plane_ignores_points_above_the_ground() -> None:
    """A trunk standing on a tilted plane does not pull the fitted plane up."""
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


def test_density_counts_layers_not_returns() -> None:
    """Many returns in one 0.1 m layer count once; the band fraction is layers / band layers."""
    points = np.array([[0.1, 0.1, 1.11], [0.1, 0.1, 1.12], [0.1, 0.1, 1.13], [0.1, 0.1, 1.55]])

    result = density_grid(points, ((1.0, 2.0),), resolution=1.0, layer=0.1)

    assert np.isclose(result.occupancy[0, 0, 0], 2 / 10)
