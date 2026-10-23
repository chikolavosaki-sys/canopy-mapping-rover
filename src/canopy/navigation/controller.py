"""Obstacle-avoidance state machine: FORWARD, TURN_LEFT, TURN_RIGHT, STOP.

Plain-language rules, checked every step:

1. If every direction is blocked very close by, STOP.
2. If the corridor straight ahead is closer than the safety distance, turn
   in place, immediately (no delay when something is in the way).
3. Pick the turn side once (the more open side, nudged towards the goal) and
   keep it until the way ahead is clear. This "commitment" stops the rover
   flipping left-right-left in front of a tree.
4. Go back to FORWARD only when the corridor is clear by the safety distance
   *plus* a margin. Using a higher bar to leave than to enter is hysteresis:
   it stops rapid FORWARD/TURN flicker at the threshold.
5. While driving FORWARD, steer towards the goal only if that direction is
   clear; otherwise keep going straight until the obstacle is passed.
"""

from enum import Enum

import numpy as np

from canopy.config import section

_NAV = section("navigation")


class MotionState(str, Enum):
    """Discrete rover movement command."""

    FORWARD = "FORWARD"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    STOP = "STOP"


TURNING = (MotionState.TURN_LEFT, MotionState.TURN_RIGHT)


class Controller:
    """Choose a movement state and a steering change from obstacle distances."""

    def __init__(
        self,
        safety_distance: float = _NAV["safety_distance_m"],
        clear_margin: float = _NAV["clear_margin_m"],
        goal_heading_weight: float = _NAV["goal_heading_weight"],
        stop_distance_fraction: float = _NAV["stop_distance_fraction"],
        forward_radius: float = _NAV["forward_radius_m"],
        max_forward_turn_deg: float = _NAV["forward_turn_max_deg"],
        fov_deg: float = _NAV["sector_fov_deg"],
    ) -> None:
        if safety_distance <= 0 or clear_margin < 0:
            raise ValueError("safety_distance must be positive and clear_margin non-negative")
        self.safety_distance = safety_distance
        self.clear_margin = clear_margin
        self.stop_distance = safety_distance * stop_distance_fraction
        self.goal_bonus = goal_heading_weight * forward_radius
        self.forward_radius = forward_radius
        self.max_forward_turn = np.deg2rad(max_forward_turn_deg)
        self.half_fov = np.deg2rad(fov_deg) / 2
        self.state = MotionState.FORWARD

    def update(
        self, sector_distances: np.ndarray, corridor: float, goal_heading: float = 0.0
    ) -> MotionState:
        """Return the next state; ``goal_heading`` is the goal angle (rad, +left)."""
        sectors = _check_sectors(sector_distances)
        turning = self.state in TURNING
        needed = self.safety_distance + (self.clear_margin if turning else 0.0)
        if np.all(sectors < self.stop_distance):
            self.state = MotionState.STOP
        elif corridor >= needed:
            self.state = MotionState.FORWARD
        elif not turning:
            self.state = self._pick_side(sectors, goal_heading)
        return self.state

    def forward_steering(self, sector_distances: np.ndarray, goal_heading: float) -> float:
        """Heading change (rad) while driving: towards the goal only if that way is clear."""
        sectors = _check_sectors(sector_distances)
        angle = float(np.clip(goal_heading, -self.half_fov, self.half_fov - 1e-9))
        edges = np.linspace(-self.half_fov, self.half_fov, len(sectors) + 1)
        goal_sector = int(np.searchsorted(edges, angle, side="right") - 1)
        if sectors[goal_sector] < self.safety_distance + self.clear_margin:
            return 0.0
        return float(np.clip(goal_heading, -self.max_forward_turn, self.max_forward_turn))

    def _pick_side(self, sectors: np.ndarray, goal_heading: float) -> MotionState:
        """Turn towards the more open side, with a bonus for the goal's side."""
        middle = len(sectors) // 2
        open_space = np.minimum(sectors, self.forward_radius)
        right = float(np.mean(open_space[:middle]))
        left = float(np.mean(open_space[middle + 1 :]))
        if goal_heading > 0:
            left += self.goal_bonus
        elif goal_heading < 0:
            right += self.goal_bonus
        return MotionState.TURN_LEFT if left >= right else MotionState.TURN_RIGHT


def _check_sectors(sector_distances: np.ndarray) -> np.ndarray:
    sectors = np.asarray(sector_distances, dtype=float)
    if sectors.ndim != 1 or len(sectors) < 3:
        raise ValueError("at least three sector distances are required")
    return sectors
