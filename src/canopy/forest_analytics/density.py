"""Vegetation density per XY cell and height band, from height-layer occupancy.

Each XY cell is a column of thin height layers (0.1 m). A layer is "occupied"
if any point falls in it. Density in a band is the fraction of its layers
that are occupied. Counting layers instead of raw points means a cell close
to the scanner (which collects many more returns) does not look denser than
an equally full cell far away.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from canopy.config import load_config

_CONFIG = load_config()


@dataclass(frozen=True)
class LayerGrid:
    """Occupied height layers: ``occupied[i, j, k]`` is cell (i, j), layer k."""

    origin: tuple[float, float]
    resolution: float
    layer: float
    occupied: NDArray[np.bool_]

    def layer_index(self, height: float) -> int:
        """Index of the layer containing ``height`` (clipped to the grid)."""
        return int(np.clip(np.floor(height / self.layer), 0, self.occupied.shape[2]))


@dataclass(frozen=True)
class DensityGrid:
    """Occupancy fraction in [0, 1] per cell and height band."""

    origin: tuple[float, float]
    resolution: float
    bands: tuple[tuple[float, float], ...]
    occupancy: NDArray[np.float64]


def layer_grid(
    points: ArrayLike, resolution: float, layer: float, top: float
) -> LayerGrid:
    """Mark occupied height layers from 0 to ``top`` m; the grid is aligned to whole cells."""
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3 or resolution <= 0 or layer <= 0:
        raise ValueError("points must be (N, 3), with positive resolutions")
    origin = np.floor(values[:, :2].min(axis=0) / resolution) * resolution
    shape = np.floor((values[:, :2].max(axis=0) - origin) / resolution).astype(int) + 1
    layers = int(np.ceil(top / layer))
    occupied = np.zeros((*shape, layers), dtype=bool)
    keep = (values[:, 2] >= 0) & (values[:, 2] < top)
    cells = np.floor((values[keep, :2] - origin) / resolution).astype(int)
    heights = np.floor(values[keep, 2] / layer).astype(int)
    occupied[cells[:, 0], cells[:, 1], heights] = True
    return LayerGrid(tuple(origin), resolution, layer, occupied)


def density_grid(
    points: ArrayLike,
    bands: tuple[tuple[float, float], ...] = tuple(map(tuple, _CONFIG["density"]["bands_m"])),
    resolution: float = _CONFIG["density"]["grid_size_m"],
    layer: float = _CONFIG["voxel_size_m"],
) -> DensityGrid:
    """Fraction of occupied layers per cell and height band; open bands end at the top point."""
    values = np.asarray(points, dtype=float)
    top = max(float(values[:, 2].max()) + layer, max(b[1] for b in bands if np.isfinite(b[1])))
    grid = layer_grid(values, resolution, layer, top)
    output = np.zeros((*grid.occupied.shape[:2], len(bands)))
    for index, (lower, upper) in enumerate(bands):
        first, last = grid.layer_index(lower), grid.layer_index(min(upper, top))
        if last > first:
            output[:, :, index] = grid.occupied[:, :, first:last].mean(axis=2)
    return DensityGrid(grid.origin, resolution, bands, output)
