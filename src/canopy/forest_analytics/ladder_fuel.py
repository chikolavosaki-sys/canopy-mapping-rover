"""Ladder-fuel proxy: how continuously vegetation connects the ground to the crowns.

Per 1 m cell, from height-normalised, stem-free points:

- occupancy 1-4 m and 1-8 m: fraction of 0.1 m height layers that hold any
  vegetation (the definition in docs/decisions.md);
- vertical gap: the tallest run of empty layers between the litter layer
  (0.3 m) and the crown base (lowest occupied layer from 4 m up; without a
  crown, the search top). Continuity = 1 - gap / gap_norm, so a gap of
  ``gap_norm_m`` or more means "no ladder".

index = w1 * occupancy(1-4) + w2 * occupancy(1-8) + w3 * continuity, in [0, 1].
Remove stem points first: a trunk is a perfect but meaningless "ladder".
This is a proxy validated against shrub labels, not a fire-behaviour model.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray

from canopy.config import section

from .density import layer_grid

_LADDER = section("ladder_fuel")
FEATURES = ("occupancy_1_4", "occupancy_1_8", "gap_m", "continuity", "ladder_fuel_index")


@dataclass(frozen=True)
class LadderFuel:
    """Per-cell ladder-fuel features on one grid (arrays of shape (nx, ny))."""

    origin: tuple[float, float]
    resolution: float
    occupancy_1_4: NDArray[np.float64]
    occupancy_1_8: NDArray[np.float64]
    gap_m: NDArray[np.float64]
    continuity: NDArray[np.float64]
    ladder_fuel_index: NDArray[np.float64]


def ladder_fuel(
    points: ArrayLike,
    resolution: float = _LADDER["grid_size_m"],
    weights: tuple[float, ...] = tuple(_LADDER["weights"]),
) -> LadderFuel:
    """Compute the ladder-fuel features and index for height-normalised points."""
    if len(weights) != 3 or not np.isclose(sum(weights), 1.0):
        raise ValueError("need three weights (occ 1-4, occ 1-8, continuity) summing to 1")
    layer = _LADDER["occupancy_voxel_m"]
    grid = layer_grid(points, resolution, layer, _LADDER["crown_search_max_m"])
    (low1, high1), (low2, high2) = _LADDER["bands_m"]
    occ_1_4 = grid.occupied[:, :, grid.layer_index(low1) : grid.layer_index(high1)].mean(axis=2)
    occ_1_8 = grid.occupied[:, :, grid.layer_index(low2) : grid.layer_index(high2)].mean(axis=2)
    gap = _largest_gap(grid.occupied, grid.layer_index) * layer
    continuity = 1.0 - np.clip(gap / _LADDER["gap_norm_m"], 0.0, 1.0)
    index = weights[0] * occ_1_4 + weights[1] * occ_1_8 + weights[2] * continuity
    return LadderFuel(grid.origin, resolution, occ_1_4, occ_1_8, gap, continuity, index)


def ladder_fuel_index(
    points: ArrayLike, resolution: float = _LADDER["grid_size_m"]
) -> tuple[NDArray[np.float64], tuple[float, float]]:
    """Shortcut returning only the index grid and its origin."""
    result = ladder_fuel(points, resolution)
    return result.ladder_fuel_index, result.origin


def save_ladder_report(result: LadderFuel, out_dir: str | Path) -> None:
    """Write ``ladder_fuel.csv`` (all features per cell) and a ``ladder_fuel.png`` heatmap."""
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    lines = ["x,y," + ",".join(FEATURES)]
    for (i, j), _ in np.ndenumerate(result.ladder_fuel_index):
        x = result.origin[0] + (i + 0.5) * result.resolution
        y = result.origin[1] + (j + 0.5) * result.resolution
        values = (getattr(result, name)[i, j] for name in FEATURES)
        lines.append(f"{x:.2f},{y:.2f}," + ",".join(f"{value:.4f}" for value in values))
    (destination / "ladder_fuel.csv").write_text("\n".join(lines) + "\n")
    _save_heatmap(result, destination / "ladder_fuel.png")


def _largest_gap(occupied: NDArray[np.bool_], layer_index) -> NDArray[np.float64]:
    """Tallest run of empty layers (in layers) from the litter layer to the crown base."""
    surface, crown = layer_index(_LADDER["surface_min_m"]), layer_index(_LADDER["crown_min_m"])
    layers = occupied.shape[2]
    above_crown_min = occupied[:, :, crown:]
    has_crown = above_crown_min.any(axis=2)
    crown_base = np.where(has_crown, crown + np.argmax(above_crown_min, axis=2), layers)
    depth = np.arange(layers)
    empty = ~occupied & (depth >= surface) & (depth[None, None, :] < crown_base[:, :, None])
    count = np.cumsum(empty, axis=2)
    last_reset = np.maximum.accumulate(np.where(empty, 0, count), axis=2)
    return (count - last_reset).max(axis=2).astype(float)


def _save_heatmap(result: LadderFuel, path: Path) -> None:
    """Map of the index in metres, single-hue scale, with a labelled colour bar."""
    import matplotlib.pyplot as plt

    nx, ny = result.ladder_fuel_index.shape
    extent = (
        result.origin[0], result.origin[0] + nx * result.resolution,
        result.origin[1], result.origin[1] + ny * result.resolution,
    )
    figure, axis = plt.subplots(figsize=(6, 5), facecolor="#fcfcfb")
    image = axis.imshow(result.ladder_fuel_index.T, origin="lower", extent=extent,
                        cmap="Oranges", vmin=0, vmax=1)
    bar = figure.colorbar(image, ax=axis, shrink=0.85)
    bar.set_label("Ladder-fuel index (0 = none, 1 = continuous)", color="#52514e")
    axis.set_title("Ladder-fuel proxy per 1 m cell", loc="left", color="#0b0b0b")
    axis.set_xlabel("x (m)", color="#52514e")
    axis.set_ylabel("y (m)", color="#52514e")
    for spine in axis.spines.values():
        spine.set_visible(False)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)
