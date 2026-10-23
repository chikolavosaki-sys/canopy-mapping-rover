"""Short-term obstacle memory.

A LiDAR mounted 0.6 m up with its lowest beam 15 deg down cannot see low
objects closer than about 1-2 m (its blind zone). A memoryless rover forgets
a rock as soon as it gets close. So we keep the obstacle points from the
last few scans, stored in map coordinates, and re-express them in the
rover's current frame each step. In the simulator the rover's pose is exact;
on a real rover it would come from odometry.
"""

from collections import deque

import numpy as np

from canopy.config import section

_NAV = section("navigation")


class ObstacleMemory:
    """Remember obstacle-height points from the last ``scans`` scans."""

    def __init__(self, scans: int = _NAV["memory_scans"]) -> None:
        if scans < 1:
            raise ValueError("scans must be at least 1")
        self._frames: deque[np.ndarray] = deque(maxlen=scans)

    def update(self, local: np.ndarray, pose: np.ndarray) -> np.ndarray:
        """Add one rover-frame scan (z = height above ground); return all remembered points.

        The result is in the current rover frame, with the same z meaning.
        Only points between ground clearance and rover height are kept.
        """
        values = np.asarray(local, dtype=float)
        tall = values[
            (values[:, 2] >= _NAV["obstacle_min_height_m"])
            & (values[:, 2] <= _NAV["rover_height_m"])
        ]
        rotation, position = pose[:2, :2], pose[:2, 3]
        world_xy = tall[:, :2] @ rotation.T + position
        self._frames.append(np.column_stack((world_xy, tall[:, 2])))
        remembered = np.vstack(self._frames)
        current_xy = (remembered[:, :2] - position) @ rotation
        return np.column_stack((current_xy, remembered[:, 2]))
