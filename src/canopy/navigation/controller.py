"""Hysteretic obstacle-avoidance state machine."""

from enum import Enum

import numpy as np


class MotionState(str, Enum):
    """Discrete rover movement command."""

    FORWARD = "FORWARD"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    STOP = "STOP"


class Controller:
    """Choose movement while avoiding abrupt state oscillation."""

    def __init__(
        self,
        safety_distance: float = 1.5,
        hysteresis_steps: int = 3,
        goal_heading_weight: float = 0.25,
    ) -> None:
        if safety_distance <= 0 or hysteresis_steps < 1:
            raise ValueError("safety_distance must be positive and hysteresis_steps >= 1")
        self.safety_distance = safety_distance
        self.hysteresis_steps = hysteresis_steps
        self.goal_heading_weight = goal_heading_weight
        self.state = MotionState.FORWARD
        self._pending = self.state
        self._pending_count = 0

    def update(self, sector_distances: np.ndarray, goal_heading: float = 0.0) -> MotionState:
        """Return a command using central clearance and goal-heading bias."""
        distances = np.asarray(sector_distances, dtype=float)
        if distances.ndim != 1 or len(distances) < 3:
            raise ValueError("at least three sector distances are required")
        middle = len(distances) // 2
        central = distances[max(0, middle - 1) : middle + 2]
        if np.all(central < self.safety_distance / 2):
            proposed = MotionState.STOP
        elif np.min(central) >= self.safety_distance:
            proposed = MotionState.FORWARD
        else:
            left = np.mean(distances[middle + 1 :])
            right = np.mean(distances[:middle])
            bias = self.goal_heading_weight * np.sign(goal_heading)
            proposed = MotionState.TURN_LEFT if left + bias >= right else MotionState.TURN_RIGHT
        if proposed == self.state:
            self._pending = proposed
            self._pending_count = 0
        elif proposed == self._pending:
            self._pending_count += 1
            if self._pending_count >= self.hysteresis_steps:
                self.state = proposed
                self._pending_count = 0
        else:
            self._pending, self._pending_count = proposed, 1
        return self.state
