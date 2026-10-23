"""Ladder-fuel occupancy proxy and small report writers."""

from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .density import density_grid


def ladder_fuel_index(
    points: ArrayLike, resolution: float = 1.0, voxel_size: float = 0.1
) -> tuple[NDArray[np.float64], tuple[float, float]]:
    """Return a [0, 1] per-cell score from 1-4 m and 1-8 m occupancy."""
    result = density_grid(points, ((1.0, 4.0), (1.0, 8.0)), resolution, voxel_size)
    occupancy = result.occupancy
    maximum = occupancy.max(axis=(0, 1), keepdims=True)
    scaled = np.divide(occupancy, maximum, out=np.zeros_like(occupancy), where=maximum > 0)
    score = 0.7 * scaled[:, :, 0] + 0.3 * scaled[:, :, 1]
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
