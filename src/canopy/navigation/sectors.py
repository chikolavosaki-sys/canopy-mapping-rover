"""Obstacle summaries for simulator navigation.

Points are in the rover frame: +X forward, +Y left, z = height above the
rover's base. Points below ``obstacle_min_height_m`` (ground) or above the
rover are not obstacles.
"""

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
    """Return the nearest obstacle distance in each forward angular sector.

    Sectors split ``fov_deg`` evenly, ordered from right (-Y) to left (+Y).
    An empty sector reports ``inf``.
    """
    values = _obstacles(points, forward_radius, rover_height, min_height)
    if sector_count < 1:
        raise ValueError("sector_count must be positive")
    output = np.full(sector_count, np.inf)
    distances = np.linalg.norm(values[:, :2], axis=1)
    angles = np.arctan2(values[:, 1], values[:, 0])
    half_fov = np.deg2rad(fov_deg) / 2
    sectors = np.searchsorted(np.linspace(-half_fov, half_fov, sector_count + 1), angles) - 1
    inside = (sectors >= 0) & (sectors < sector_count)
    np.minimum.at(output, sectors[inside], distances[inside])
    return output


def corridor_clearance(
    points: np.ndarray,
    half_width: float = _NAV["rover_radius_m"] + _NAV["corridor_margin_m"],
    forward_radius: float = _NAV["forward_radius_m"],
    rover_height: float = _NAV["rover_height_m"],
    min_height: float = _NAV["obstacle_min_height_m"],
) -> float:
    """Return how far the rover can drive straight ahead before hitting something.

    Only obstacles inside a straight corridor as wide as the rover (plus a
    margin) count, so a tree beside the path does not block it, while a tree
    slightly off-centre but in the rover's way does.
    """
    values = _obstacles(points, forward_radius, rover_height, min_height)
    ahead = values[np.abs(values[:, 1]) <= half_width, 0]
    return float(ahead.min()) if len(ahead) else np.inf


def footprint_clearance(
    points: np.ndarray,
    position: np.ndarray,
    rover_height: float = _NAV["rover_height_m"],
    min_height: float = _NAV["obstacle_min_height_m"],
) -> float:
    """Return the distance from a rover-frame XY position to the nearest sensed obstacle.

    Unlike the corridor, this also sees obstacles beside or slightly behind the
    rover, which matters when it steers past something at its flank.
    """
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    tall = values[(values[:, 2] >= min_height) & (values[:, 2] <= rover_height), :2]
    if not len(tall):
        return np.inf
    return float(np.min(np.linalg.norm(tall - np.asarray(position)[:2], axis=1)))


def _obstacles(
    points: np.ndarray, forward_radius: float, rover_height: float, min_height: float
) -> np.ndarray:
    """Keep points in front of the rover, within range, between ground and rover height."""
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    mask = (
        (values[:, 0] > 0)
        & (np.linalg.norm(values[:, :2], axis=1) <= forward_radius)
        & (values[:, 2] >= min_height)
        & (values[:, 2] <= rover_height)
    )
    return values[mask]
