"""Tests for ladder-fuel ranking and DBH fitting."""

import numpy as np

from canopy.forest_analytics.ladder_fuel import ladder_fuel_index
from canopy.forest_analytics.stems import detect_stems


def test_shrub_cell_scores_above_open_cell() -> None:
    """A cell containing low vegetation receives the larger proxy score."""
    open_cell = np.array([[0.2, 0.2, 0.2]])
    shrub = np.array([[2.1, 2.1, height] for height in np.linspace(1.0, 3.9, 30)])

    score, _ = ladder_fuel_index(np.vstack((open_cell, shrub)), resolution=1.0, voxel_size=0.1)

    assert score[1, 1] > score[0, 0]


def test_stem_circle_fit_recovers_dbh() -> None:
    """A clean synthetic stem is detected with a close diameter estimate."""
    angles = np.linspace(0, 2 * np.pi, 40, endpoint=False)
    points = np.vstack(
        [
            [2 + 0.15 * np.cos(angle), 3 + 0.15 * np.sin(angle), height]
            for height in (1.21, 1.30, 1.39)
            for angle in angles
        ]
    )

    stems = detect_stems(points, radius=0.5, min_points=20, max_residual=0.01)

    assert len(stems) == 1
    assert abs(stems[0].dbh - 0.30) < 0.01
