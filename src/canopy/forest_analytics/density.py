"""Occupancy density by XY cell and height band."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from canopy.config import load_config

_CONFIG = load_config()


@dataclass(frozen=True)
class DensityGrid:
    """Grid coordinates and occupancy fractions for named height bands."""

    origin: tuple[float, float]
    resolution: float
    bands: tuple[tuple[float, float], ...]
    occupancy: NDArray[np.float64]


def density_grid(
    points: ArrayLike,
    bands: tuple[tuple[float, float], ...],
    resolution: float = _CONFIG["density"]["grid_size_m"],
    voxel_size: float = _CONFIG["voxel_size_m"],
) -> DensityGrid:
    """Compute occupied vertical voxels per XY cell and band.

    Occupancy uses voxels instead of raw returns so a nearby scan angle with
    more samples does not automatically look denser than a distant one.
    """
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3 or resolution <= 0 or voxel_size <= 0:
        raise ValueError("points must be (N, 3), with positive resolutions")
    origin = values[:, :2].min(axis=0)
    shape = np.floor((values[:, :2].max(axis=0) - origin) / resolution).astype(int) + 1
    output = np.zeros((*shape, len(bands)), dtype=float)
    cells = np.floor((values[:, :2] - origin) / resolution).astype(int)
    for band_index, (lower, upper) in enumerate(bands):
        selected = values[(values[:, 2] >= lower) & (values[:, 2] < upper)]
        selected_cells = cells[(values[:, 2] >= lower) & (values[:, 2] < upper)]
        keys = np.floor(selected / voxel_size).astype(int)
        unique = np.unique(np.column_stack((selected_cells, keys[:, 2])), axis=0)
        for x, y, _ in unique:
            output[x, y, band_index] += 1
    return DensityGrid(tuple(origin), resolution, bands, output)
