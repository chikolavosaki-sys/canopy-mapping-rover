"""Ground modelling and height normalization."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from canopy.config import section

_GROUND = section("ground")


@dataclass(frozen=True)
class GroundModel:
    """Lowest-observed ground estimate on a regular XY grid."""

    origin: tuple[float, float]
    resolution: float
    elevations: NDArray[np.float64]


def fit_ground(
    points: ArrayLike,
    resolution: float = _GROUND["grid_size_m"],
    quantile: float = _GROUND["lowest_quantile"],
) -> GroundModel:
    """Fit a robust grid-lowest-point digital terrain model."""
    values = _points(points)
    if resolution <= 0 or not 0 < quantile <= 1:
        raise ValueError("resolution must be positive and quantile must be in (0, 1]")
    origin = values[:, :2].min(axis=0)
    shape = np.floor((values[:, :2].max(axis=0) - origin) / resolution).astype(int) + 1
    grid = np.full(shape, np.nan)
    cells = np.floor((values[:, :2] - origin) / resolution).astype(int)
    for index in np.ndindex(tuple(shape)):
        heights = values[np.all(cells == index, axis=1), 2]
        if len(heights):
            grid[index] = np.quantile(heights, quantile)
    return GroundModel(tuple(origin), resolution, _fill_missing(grid))


def normalize_heights(
    points: ArrayLike,
    resolution: float = _GROUND["grid_size_m"],
    quantile: float = _GROUND["lowest_quantile"],
) -> tuple[GroundModel, NDArray[np.float64]]:
    """Return a ground model and each point's height above its local ground."""
    values = _points(points)
    model = fit_ground(values, resolution, quantile)
    cells = np.floor((values[:, :2] - model.origin) / model.resolution).astype(int)
    cells = np.clip(cells, 0, np.array(model.elevations.shape) - 1)
    ground = model.elevations[cells[:, 0], cells[:, 1]]
    normalized = values.copy()
    normalized[:, 2] -= ground
    return model, normalized


def lowest_per_cell(points: ArrayLike, cell_size: float) -> NDArray[np.int64]:
    """Indices of the lowest point in each occupied XY cell (likely ground)."""
    values = _points(points)
    cells = np.floor(values[:, :2] / cell_size).astype(np.int64)
    order = np.lexsort((values[:, 2], cells[:, 1], cells[:, 0]))
    _, first = np.unique(cells[order], axis=0, return_index=True)
    return order[first]


def fit_plane_ransac(
    points: ArrayLike, distance: float, iterations: int, seed: int = 0
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Fit ``z = a x + b y + c`` robustly; return ``(a, b, c)`` and the inlier mask.

    RANSAC: try planes through random triples of points, keep the one with the
    most points within ``distance``, then refine it by least squares on those
    inliers. Points on trunks or shrubs do not pull the plane up.
    """
    values = _points(points)
    if len(values) < 3:
        raise ValueError("need at least three points to fit a plane")
    rng = np.random.default_rng(seed)
    design = np.column_stack((values[:, :2], np.ones(len(values))))
    best = np.zeros(len(values), dtype=bool)
    for _ in range(iterations):
        sample = rng.choice(len(values), 3, replace=False)
        try:
            plane = np.linalg.solve(design[sample], values[sample, 2])
        except np.linalg.LinAlgError:
            continue
        inliers = np.abs(design @ plane - values[:, 2]) <= distance
        if inliers.sum() > best.sum():
            best = inliers
    if best.sum() < 3:
        best[:] = True
    plane = np.linalg.lstsq(design[best], values[best, 2], rcond=None)[0]
    return plane, best


def _points(points: ArrayLike) -> NDArray[np.float64]:
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    return values


def _fill_missing(grid: NDArray[np.float64]) -> NDArray[np.float64]:
    if np.all(np.isfinite(grid)):
        return grid
    fallback = float(np.nanmedian(grid))
    return np.where(np.isfinite(grid), grid, fallback)
