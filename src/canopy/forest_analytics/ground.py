"""Ground modelling and height normalization."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True)
class GroundModel:
    """Lowest-observed ground estimate on a regular XY grid."""

    origin: tuple[float, float]
    resolution: float
    elevations: NDArray[np.float64]


def fit_ground(points: ArrayLike, resolution: float = 1.0, quantile: float = 0.1) -> GroundModel:
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
    points: ArrayLike, resolution: float = 1.0, quantile: float = 0.1
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
