"""Short-term obstacle memory.

A mounted LiDAR can lose sight of a nearby rock below its lowest beam. We
keep map XY and estimated height above the ground under each obstacle, then
re-express XY in the level rover frame each step. The simulator supplies the
rover pose directly.
"""

from collections import deque

import numpy as np

from canopy.config import section

from .sectors import DETECTION_HEIGHT

_NAV = section("navigation")


class ObstacleMemory:
    """Remember obstacle-height points from the last ``scans`` scans."""

    def __init__(self, scans: int = _NAV["memory_scans"]) -> None:
        if scans < 1:
            raise ValueError("scans must be at least 1")
        self._frames: deque[np.ndarray] = deque(maxlen=scans)

    def update(self, local: np.ndarray, pose: np.ndarray) -> np.ndarray:
        """Add one ground-normalised scan and return all remembered points.

        XY follows the rover's position and heading. The third column is
        each point's estimated height above the terrain at its own XY.
        Rover elevation changes leave that clearance measurement unchanged.
        """
        values = np.asarray(local, dtype=float)
        tall = values[
            (values[:, 2] >= DETECTION_HEIGHT)
            & (values[:, 2] <= _NAV["rover_height_m"])
        ]
        rotation, position = pose[:2, :2], pose[:2, 3]
        world_xy = tall[:, :2] @ rotation.T + position
        self._frames.append(np.column_stack((world_xy, tall[:, 2])))
        remembered = np.vstack(self._frames)
        current_xy = (remembered[:, :2] - position) @ rotation
        heights_above_local_ground = remembered[:, 2]
        return np.column_stack((current_xy, heights_above_local_ground))
