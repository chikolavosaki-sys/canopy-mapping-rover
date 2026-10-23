"""Tests for the synthetic forest test backbone."""

import numpy as np

from canopy.simulation.synthetic_forest import Forest, Sensor, make_forest, simulate_scan


def test_forest_generation_is_reproducible_and_labelled() -> None:
    """The same seed creates identical points and semantic labels."""
    first = make_forest(seed=7, plot_size_m=20, n_trees=4)
    second = make_forest(seed=7, plot_size_m=20, n_trees=4)

    np.testing.assert_allclose(first.points, second.points)
    np.testing.assert_array_equal(first.labels, second.labels)
    assert set(first.labels) == {"ground", "stem", "crown", "shrub", "rock"}
    assert len(first.trees) == 4


def test_nearer_point_occludes_farther_point() -> None:
    """One angular beam returns the nearest point in its direction."""
    forest = Forest(
        points=np.array([[3.0, 0.0, 0.0], [6.0, 0.0, 0.0]]),
        labels=np.array(["stem", "crown"]),
        trees=[],
        shrubs=[],
        plot_size_m=10,
    )
    scan = simulate_scan(
        forest,
        np.eye(4),
        Sensor(beam_count=1, horizontal_samples=1, vertical_fov_deg=2, max_range_m=10),
    )

    assert len(scan) == 1
    np.testing.assert_allclose(scan[0], [3.0, 0.0, 0.0], atol=0.1)
