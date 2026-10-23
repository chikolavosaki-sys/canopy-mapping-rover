"""Stem clustering and DBH circle fitting."""

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass(frozen=True)
class Stem:
    """Estimated tree stem at breast height."""

    x: float
    y: float
    dbh: float
    fit_residual: float
    n_points: int


def detect_stems(
    points: ArrayLike,
    slice_min: float = 1.2,
    slice_max: float = 1.4,
    radius: float = 0.8,
    min_points: int = 20,
    min_dbh: float = 0.05,
    max_dbh: float = 0.60,
    max_residual: float = 0.05,
) -> list[Stem]:
    """Cluster a breast-height slice and fit circles with least squares."""
    values = np.asarray(points, dtype=float)
    selected = values[(values[:, 2] >= slice_min) & (values[:, 2] < slice_max), :2]
    clusters = _clusters(selected, radius)
    stems = []
    for cluster in clusters:
        if len(cluster) < min_points:
            continue
        centre, fitted_radius, residual = _fit_circle(cluster)
        dbh = 2 * fitted_radius
        if min_dbh <= dbh <= max_dbh and residual <= max_residual:
            stems.append(Stem(*centre, dbh, residual, len(cluster)))
    return stems


def stems_to_rows(stems: list[Stem]) -> list[dict[str, float | int]]:
    """Convert stem dataclasses to CSV-compatible rows."""
    return [asdict(stem) for stem in stems]


def _clusters(points: np.ndarray, radius: float) -> list[np.ndarray]:
    labels = np.full(len(points), -1, dtype=int)
    clusters = []
    for index in range(len(points)):
        if labels[index] >= 0:
            continue
        members = np.flatnonzero(np.linalg.norm(points - points[index], axis=1) <= radius)
        label = len(clusters)
        labels[members] = label
        clusters.append(points[members])
    return clusters


def _fit_circle(points: np.ndarray) -> tuple[np.ndarray, float, float]:
    matrix = np.column_stack((2 * points[:, 0], 2 * points[:, 1], np.ones(len(points))))
    target = np.sum(points**2, axis=1)
    centre_x, centre_y, constant = np.linalg.lstsq(matrix, target, rcond=None)[0]
    centre = np.array([centre_x, centre_y])
    distances = np.linalg.norm(points - centre, axis=1)
    residual = np.sqrt(np.mean((distances - distances.mean()) ** 2))
    return centre, float(np.mean(distances)), float(residual)
