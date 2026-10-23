"""The rover's own ground estimate, from a single scan.

On a slope, "z above the rover's wheels" is a bad obstacle test: going uphill,
the ground ahead is higher than the rover, and would look like a wall. So
each scan we take the lowest point in every 1 m cell (usually ground), fit a
plane to those with RANSAC (which ignores cells where a trunk was lowest),
and measure every point's height above that plane instead.
"""

import numpy as np

from canopy.config import section
from canopy.forest_analytics.ground import fit_plane_ransac, lowest_per_cell

_TERRAIN = section("navigation")["terrain"]


def heights_above_ground(points: np.ndarray) -> np.ndarray:
    """Return a copy of rover-frame points with z replaced by height above the fitted ground."""
    values = np.asarray(points, dtype=float)
    if len(values) < 3:
        return values.copy()
    candidates = values[lowest_per_cell(values, _TERRAIN["cell_size_m"])]
    if len(candidates) < 3:
        return values.copy()
    plane, _ = fit_plane_ransac(
        candidates, _TERRAIN["ransac_distance_m"], _TERRAIN["ransac_iterations"]
    )
    result = values.copy()
    result[:, 2] -= values[:, 0] * plane[0] + values[:, 1] * plane[1] + plane[2]
    return result
