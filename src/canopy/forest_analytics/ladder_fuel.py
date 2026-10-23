"""Ladder-fuel occupancy proxy and small report writers."""

from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray

from canopy.config import section

from .density import density_grid

_LADDER = section("ladder_fuel")


def ladder_fuel_index(
    points: ArrayLike,
    resolution: float = _LADDER["grid_size_m"],
    voxel_size: float = _LADDER["occupancy_voxel_m"],
    bands: tuple[tuple[float, float], ...] = tuple(map(tuple, _LADDER["bands_m"])),
    weights: tuple[float, ...] = tuple(_LADDER["band_weights"]),
) -> tuple[NDArray[np.float64], tuple[float, float]]:
    """Return a [0, 1] per-cell score from weighted height-band occupancy.

    Each band's occupancy is scaled by its plot maximum, so the score ranks
    cells within one plot; it is not comparable across plots. Weights must
    sum to 1 to keep the score in [0, 1].
    """
    if len(bands) != len(weights) or not np.isclose(sum(weights), 1.0):
        raise ValueError("need one weight per band, and weights must sum to 1")
    result = density_grid(points, bands, resolution, voxel_size)
    occupancy = result.occupancy
    maximum = occupancy.max(axis=(0, 1), keepdims=True)
    scaled = np.divide(occupancy, maximum, out=np.zeros_like(occupancy), where=maximum > 0)
    score = np.tensordot(scaled, np.asarray(weights), axes=([2], [0]))
    return score, result.origin


def save_ladder_report(
    score: NDArray[np.float64], origin: tuple[float, float], resolution: float, out_dir: str | Path
) -> None:
    """Write a CSV and PNG heatmap for the ladder-fuel proxy."""
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for (x, y), value in np.ndenumerate(score):
        rows.append(
            f"{origin[0] + x * resolution:.3f},"
            f"{origin[1] + y * resolution:.3f},{value:.6f}"
        )
    content = "x,y,ladder_fuel_index\n" + "\n".join(rows) + "\n"
    (destination / "ladder_fuel.csv").write_text(content)
    import matplotlib.pyplot as plt

    plt.imsave(destination / "ladder_fuel.png", score.T, vmin=0, vmax=1, cmap="YlOrRd")
