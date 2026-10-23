"""Tests for sector obstacle summaries and controller hysteresis."""

import numpy as np

from canopy.navigation import Controller, MotionState, nearest_obstacles


def test_sector_summary_finds_forward_obstacle() -> None:
    """A point in the centre sector has the expected nearest distance."""
    distances = nearest_obstacles(np.array([[2.0, 0.0, 1.0], [3.0, 2.0, 1.0]]))

    assert distances[4] == 2.0


def test_controller_waits_for_hysteresis() -> None:
    """A transient obstacle does not immediately change the command."""
    controller = Controller(safety_distance=1.5, hysteresis_steps=2)
    blocked = np.ones(9)
    blocked[4] = 1.0

    assert controller.update(blocked) == MotionState.FORWARD
    assert controller.update(blocked) != MotionState.FORWARD
