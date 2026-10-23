"""Angular obstacle summaries for simulator navigation."""

import numpy as np

from canopy.config import section

_NAV = section("navigation")


def nearest_obstacles(
    points: np.ndarray,
    sector_count: int = _NAV["sector_count"],
    forward_radius: float = _NAV["forward_radius_m"],
    rover_height: float = _NAV["rover_height_m"],
    min_height: float = _NAV["obstacle_min_height_m"],
    fov_deg: float = _NAV["sector_fov_deg"],
) -> np.ndarray:
    """Return nearest obstacle distance in each forward angular sector.

    Points are assumed to be in the rover frame: +X is forward and +Y is left.
    Points lower than ``min_height`` (ground) or above the rover are ignored.
    Sectors split ``fov_deg`` evenly, ordered from right (-Y) to left (+Y).
    """
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3 or sector_count < 1:
        raise ValueError("points must be (N, 3) and sector_count must be positive")
    distances = np.linalg.norm(values[:, :2], axis=1)
    mask = (
        (values[:, 0] > 0)
        & (distances <= forward_radius)
        & (values[:, 2] >= min_height)
        & (values[:, 2] <= rover_height)
    )
    output = np.full(sector_count, np.inf)
    angles = np.arctan2(values[:, 1], values[:, 0])
    half_fov = np.deg2rad(fov_deg) / 2
    edges = np.linspace(-half_fov, half_fov, sector_count + 1)
    for index in np.flatnonzero(mask):
        sector = np.searchsorted(edges, angles[index], side="right") - 1
        if 0 <= sector < sector_count:
            output[sector] = min(output[sector], distances[index])
    return output
