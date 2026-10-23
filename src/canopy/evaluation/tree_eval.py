"""Tree detection metrics against synthetic ground truth."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from canopy.config import section
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
    detected: list[dict[str, float | int]],
    truth: list[Tree],
    gate: float = section("evaluation")["tree_match_gate_m"],
) -> TreeMetrics:
    """Match XY tree positions within a gate and report DBH errors in metres.

    DBH RMSE and bias are NaN when nothing matched: there is no error to report,
    and 0.0 would read as a perfect result.
    """
    if gate <= 0:
        raise ValueError("gate must be positive")
    if not detected and not truth:
        return TreeMetrics(1.0, 1.0, 0.0, 0.0, 0)
    if not detected or not truth:
        return TreeMetrics(0.0, 0.0, float("nan"), float("nan"), 0)
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
    rmse = float(np.sqrt(np.mean(errors**2))) if len(errors) else float("nan")
    bias = float(np.mean(errors)) if len(errors) else float("nan")
    return TreeMetrics(
        len(matches) / len(detected),
        len(matches) / len(truth),
        rmse,
        bias,
        len(matches),
    )
