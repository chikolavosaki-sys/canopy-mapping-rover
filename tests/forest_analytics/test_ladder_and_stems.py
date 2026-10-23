"""Tests for the ladder-fuel proxy and stem detection."""

import numpy as np
import pytest

from canopy.evaluation.tree_eval import evaluate_trees
from canopy.forest_analytics.ground import normalize_heights
from canopy.forest_analytics.ladder_fuel import ladder_fuel
from canopy.forest_analytics.stems import detect_stems, remove_stem_points, stems_to_rows
from canopy.simulation.lidar import simulate_scan
from canopy.simulation.synthetic_forest import make_forest, traversal_poses


def _column(x: float, y: float, low: float, high: float) -> np.ndarray:
    """Vegetation points every 5 cm between two heights in one 1 m cell."""
    return np.array([[x, y, z] for z in np.arange(low, high, 0.05)])


def _trunk(x, y, radius, heights, arc_deg=360.0, lean_deg=0.0) -> np.ndarray:
    """Points on a (possibly partly visible, possibly leaning) trunk surface."""
    angles = np.deg2rad(np.linspace(0, arc_deg, int(arc_deg / 4), endpoint=False))
    shift = np.tan(np.deg2rad(lean_deg))
    return np.array(
        [[x + shift * z + radius * np.cos(a), y + radius * np.sin(a), z]
         for z in heights for a in angles]
    )


def test_shrub_cell_scores_above_open_cell() -> None:
    """A cell full of 1-4 m vegetation scores above an empty one."""
    points = np.vstack((_column(0.5, 0.5, 0.0, 0.05), _column(2.5, 2.5, 1.0, 3.9)))

    index = ladder_fuel(points).ladder_fuel_index

    assert index[2, 2] > index[0, 0]


def test_gap_to_the_crown_lowers_the_index() -> None:
    """Shrubs reaching the crown form a ladder; the same shrubs under a 4.5 m gap do not."""
    connected = np.vstack((_column(0.5, 0.5, 0.5, 5.5), _column(0.5, 0.5, 6.0, 8.0)))
    gapped = np.vstack((_column(2.5, 0.5, 0.5, 1.5), _column(2.5, 0.5, 6.0, 8.0)))

    result = ladder_fuel(np.vstack((connected, gapped)))

    assert result.gap_m[0, 0] < 1.0 and result.continuity[0, 0] > 0.75
    assert result.gap_m[2, 0] >= 4.0 and result.continuity[2, 0] == 0.0
    assert result.ladder_fuel_index[0, 0] > result.ladder_fuel_index[2, 0]


def test_full_trunk_is_detected_with_its_dbh() -> None:
    """A clean upright trunk is found and its diameter recovered."""
    points = _trunk(2.0, 3.0, 0.15, np.arange(0.6, 2.2, 0.05))

    stems = detect_stems(points)

    assert len(stems) == 1
    assert abs(stems[0].dbh - 0.30) < 0.005


def test_half_visible_trunk_still_gives_the_right_dbh() -> None:
    """A trunk seen from one side only (180 deg) is measured within 1 cm."""
    points = _trunk(2.0, 3.0, 0.20, np.arange(0.6, 2.2, 0.05), arc_deg=180)

    stems = detect_stems(points)

    assert len(stems) == 1 and abs(stems[0].dbh - 0.40) < 0.01


def test_leaning_trunk_and_shrub_blob_are_rejected() -> None:
    """A 30-degree lean fails verticality; a random blob fails the circle checks."""
    leaning = _trunk(2.0, 3.0, 0.15, np.arange(0.6, 2.2, 0.05), lean_deg=30)
    blob = np.random.default_rng(0).uniform([6, 6, 0.5], [7, 7, 2.5], size=(800, 3))

    assert detect_stems(leaning) == []
    assert detect_stems(blob) == []


def test_stem_points_are_removed_before_ladder_fuel() -> None:
    """Points on the detected trunk go; vegetation 1 m away stays."""
    trunk = _trunk(2.0, 3.0, 0.15, np.arange(0.6, 2.2, 0.05))
    bush = _column(3.2, 3.0, 0.5, 2.0)

    kept = remove_stem_points(np.vstack((trunk, bush)), detect_stems(trunk))

    np.testing.assert_allclose(kept, bush)


@pytest.mark.parametrize("seed", [0, 1])
def test_stems_on_a_scanned_synthetic_forest(seed) -> None:
    """On a LiDAR-scanned forest (exact poses): recall >= 0.8 and DBH RMSE <= 3 cm."""
    forest = make_forest(seed, plot_size_m=20.0, n_trees=6, points_per_tree=500)
    scan = np.vstack([simulate_scan(forest, pose, seed=i)
                      for i, pose in enumerate(traversal_poses(forest))])
    _, normalized, _ = normalize_heights(scan)

    result = evaluate_trees(stems_to_rows(detect_stems(normalized)), forest.trees)

    assert result.recall >= 0.8, f"recall {result.recall:.2f}"
    assert result.dbh_rmse <= 0.03, f"DBH RMSE {result.dbh_rmse:.3f} m"
