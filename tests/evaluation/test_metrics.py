"""Tests for Phase 5 evaluation metrics."""

import numpy as np

from canopy.evaluation.ladder_eval import evaluate_ladder
from canopy.evaluation.odometry_eval import absolute_position_error, relative_position_error
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
