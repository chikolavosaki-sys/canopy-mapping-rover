"""Tests for Phase 5 evaluation metrics."""

import numpy as np

from canopy.evaluation.ladder_eval import evaluate_ladder
from canopy.evaluation.odometry_eval import (
    absolute_position_error,
    final_drift_percent,
    relative_position_error,
    relative_to_first,
)
from canopy.evaluation.tree_eval import evaluate_trees
from canopy.simulation.synthetic_forest import Tree


def _pose(x: float) -> np.ndarray:
    pose = np.eye(4)
    pose[0, 3] = x
    return pose


def test_odometry_metrics_detect_translation_error() -> None:
    """ATE and RPE are positive for a perturbed trajectory."""
    truth = [_pose(0), _pose(1), _pose(2)]
    estimated = [_pose(0), _pose(1.1), _pose(2.2)]

    assert absolute_position_error(estimated, truth) > 0
    assert relative_position_error(estimated, truth) > 0


def test_final_drift_is_end_error_over_path_length() -> None:
    """Ending 0.2 m off after a 10 m path is 2 % drift."""
    truth = [_pose(0), _pose(5), _pose(10)]
    estimated = [_pose(0), _pose(5), _pose(10.2)]

    assert abs(final_drift_percent(estimated, truth) - 2.0) < 1e-9


def test_relative_to_first_handles_rotated_start() -> None:
    """A rotated, shifted start becomes identity and later poses follow it."""
    start = _pose(5.0)
    start[:2, :2] = [[0.0, -1.0], [1.0, 0.0]]  # facing +Y
    ahead = start.copy()
    ahead[:2, 3] += [0.0, 2.0]  # 2 m forward along +Y

    relative = relative_to_first([start, ahead])

    np.testing.assert_allclose(relative[0], np.eye(4), atol=1e-12)
    np.testing.assert_allclose(relative[1][:3, 3], [2.0, 0.0, 0.0], atol=1e-12)


def test_tree_metrics_match_within_gate() -> None:
    """A close detection receives full precision and recall."""
    result = evaluate_trees([{"x": 0.1, "y": 0.0, "dbh": 0.3}], [Tree(0, 0, 0.3, 10)])

    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.dbh_rmse == 0.0


def test_ladder_auc_prefers_shrub_cells() -> None:
    """Higher scores on positive cells produce an AUC above chance."""
    result = evaluate_ladder(np.array([0.1, 0.8, 0.2, 0.9]), np.array([0, 1, 0, 1]))

    assert result["auc"] > 0.9


def test_tree_metrics_without_matches_report_no_dbh_error() -> None:
    """A detection 3 m from the only tree is not a match, so DBH error is NaN, not 0."""
    result = evaluate_trees([{"x": 3.0, "y": 0.0, "dbh": 0.3}], [Tree(0, 0, 0.3, 10)])

    assert result.recall == 0.0 and result.precision == 0.0
    assert np.isnan(result.dbh_rmse) and np.isnan(result.dbh_bias)
