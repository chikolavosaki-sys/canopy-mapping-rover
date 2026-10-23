"""Tree detection metrics against synthetic ground truth."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from canopy.simulation.synthetic_forest import Tree


@dataclass(frozen=True)
class TreeMetrics:
    """Precision, recall, and DBH errors for gated tree matches."""

    precision: float
    recall: float
    dbh_rmse: float
    dbh_bias: float
    matches: int


def evaluate_trees(
    detected: list[dict[str, float | int]], truth: list[Tree], gate: float = 0.5
) -> TreeMetrics:
    """Match XY tree positions within a gate and report DBH errors in metres."""
    if gate <= 0:
        raise ValueError("gate must be positive")
    if not detected and not truth:
        return TreeMetrics(1.0, 1.0, 0.0, 0.0, 0)
    if not detected or not truth:
        return TreeMetrics(0.0, 0.0, 0.0, 0.0, 0)
    estimated_xy = np.array([[row["x"], row["y"]] for row in detected])
    truth_xy = np.array([[tree.x, tree.y] for tree in truth])
    distances = np.linalg.norm(estimated_xy[:, None] - truth_xy[None, :], axis=2)
    rows, columns = linear_sum_assignment(distances)
    matches = [
        (row, column)
        for row, column in zip(rows, columns)
        if distances[row, column] <= gate
    ]
    errors = np.array([detected[row]["dbh"] - truth[column].dbh for row, column in matches])
    rmse = float(np.sqrt(np.mean(errors**2))) if len(errors) else 0.0
    bias = float(np.mean(errors)) if len(errors) else 0.0
    return TreeMetrics(
        len(matches) / len(detected),
        len(matches) / len(truth),
        rmse,
        bias,
        len(matches),
    )
