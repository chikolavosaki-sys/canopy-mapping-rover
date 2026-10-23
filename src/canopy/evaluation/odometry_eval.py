"""Trajectory metrics for exact synthetic or reference trajectories."""

import numpy as np


def absolute_position_error(
    estimated: list[np.ndarray], reference: list[np.ndarray]
) -> float:
    """Return RMSE translation error after aligning both trajectories at start."""
    _check_lengths(estimated, reference)
    estimate = _positions(estimated)
    truth = _positions(reference)
    offset = truth[0] - estimate[0]
    errors = estimate + offset - truth
    return float(np.sqrt(np.mean(np.sum(errors**2, axis=1))))


def relative_position_error(
    estimated: list[np.ndarray], reference: list[np.ndarray]
) -> float:
    """Return RMSE error of consecutive translation increments."""
    _check_lengths(estimated, reference)
    estimate_delta = np.diff(_positions(estimated), axis=0)
    truth_delta = np.diff(_positions(reference), axis=0)
    if not len(estimate_delta):
        return 0.0
    return float(np.sqrt(np.mean(np.sum((estimate_delta - truth_delta) ** 2, axis=1))))


def start_to_end_drift(poses: list[np.ndarray]) -> float:
    """Return the distance between the first and final estimated positions."""
    if not poses:
        return 0.0
    positions = _positions(poses)
    return float(np.linalg.norm(positions[-1] - positions[0]))


def _positions(poses: list[np.ndarray]) -> np.ndarray:
    values = np.asarray(poses, dtype=float)
    if values.ndim != 3 or values.shape[1:] != (4, 4):
        raise ValueError("poses must contain 4x4 matrices")
    return values[:, :3, 3]


def _check_lengths(first: list[np.ndarray], second: list[np.ndarray]) -> None:
    if len(first) != len(second) or not first:
        raise ValueError("trajectories must be non-empty and have equal length")
