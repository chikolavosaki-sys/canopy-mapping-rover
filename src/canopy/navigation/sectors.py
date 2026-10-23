"""Angular obstacle summaries for simulator navigation."""

import numpy as np


def nearest_obstacles(
    points: np.ndarray,
    sector_count: int = 9,
    forward_radius: float = 8.0,
    rover_height: float = 2.0,
) -> np.ndarray:
    """Return nearest obstacle distance in each forward angular sector.

    Points are assumed to be in the rover frame: +X is forward and +Y is left.
    Ground and points above the rover are ignored.
    """
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3 or sector_count < 1:
        raise ValueError("points must be (N, 3) and sector_count must be positive")
    distances = np.linalg.norm(values[:, :2], axis=1)
    mask = (
        (values[:, 0] > 0)
        & (distances <= forward_radius)
        & (values[:, 2] >= 0.15)
        & (values[:, 2] <= rover_height)
    )
    output = np.full(sector_count, np.inf)
    angles = np.arctan2(values[:, 1], values[:, 0])
    edges = np.linspace(-np.pi / 2, np.pi / 2, sector_count + 1)
    for index in np.flatnonzero(mask):
        sector = np.searchsorted(edges, angles[index], side="right") - 1
        if 0 <= sector < sector_count:
            output[sector] = min(output[sector], distances[index])
    return output
