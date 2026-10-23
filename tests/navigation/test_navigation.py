"""Tests for obstacle summaries and the controller state machine."""

import numpy as np

from canopy.navigation import Controller, MotionState, nearest_obstacles
from canopy.navigation.sectors import corridor_clearance, footprint_clearance

OPEN = np.full(9, np.inf)


def test_sector_summary_finds_forward_obstacle() -> None:
    """A point straight ahead lands in the centre sector."""
    distances = nearest_obstacles(np.array([[2.0, 0.0, 1.0], [3.0, 2.0, 1.0]]))

    assert distances[4] == 2.0


def test_ground_and_overhead_points_are_not_obstacles() -> None:
    """Points below ground clearance or above the rover are ignored."""
    points = np.array([[2.0, 0.0, 0.1], [2.0, 0.0, 3.0]])

    assert np.all(np.isinf(nearest_obstacles(points)))
    assert corridor_clearance(points) == np.inf


def test_corridor_ignores_trees_beside_the_path() -> None:
    """Only obstacles within the rover-wide corridor block driving straight."""
    beside = np.array([[2.0, 1.5, 1.0]])
    in_the_way = np.array([[3.0, 0.4, 1.0]])

    assert corridor_clearance(beside) == np.inf
    assert corridor_clearance(in_the_way) == 3.0


def test_footprint_sees_obstacles_at_the_flank() -> None:
    """An obstacle beside the rover counts even though it is not ahead."""
    flank = np.array([[0.0, -0.5, 1.0]])

    assert abs(footprint_clearance(flank, np.array([0.25, 0.0])) - np.hypot(0.25, 0.5)) < 1e-12


def test_controller_reacts_immediately_to_a_blocked_corridor() -> None:
    """No delay: the first blocked reading already starts a turn."""
    controller = Controller(safety_distance=1.5)

    assert controller.update(OPEN, corridor=1.0) in (MotionState.TURN_LEFT, MotionState.TURN_RIGHT)


def test_controller_keeps_its_turn_side_until_clear() -> None:
    """Once turning left, a now more-open right side does not cause flip-flopping."""
    controller = Controller(safety_distance=1.5)
    left_open = np.array([1, 1, 1, 1, 1, 8, 8, 8, 8], dtype=float)
    right_open = left_open[::-1]

    assert controller.update(left_open, corridor=1.0) == MotionState.TURN_LEFT
    assert controller.update(right_open, corridor=1.0) == MotionState.TURN_LEFT


def test_controller_needs_extra_margin_to_resume_forward() -> None:
    """Hysteresis: entering avoidance at < 1.5 m, leaving only at >= 1.5 + 0.5 m."""
    controller = Controller(safety_distance=1.5, clear_margin=0.5)
    controller.update(OPEN, corridor=1.0)

    assert controller.update(OPEN, corridor=1.8) != MotionState.FORWARD
    assert controller.update(OPEN, corridor=2.1) == MotionState.FORWARD
    assert controller.update(OPEN, corridor=1.6) == MotionState.FORWARD


def test_controller_stops_when_boxed_in() -> None:
    """Every direction blocked very close by means STOP."""
    controller = Controller(safety_distance=1.5)

    assert controller.update(np.full(9, 0.3), corridor=0.3) == MotionState.STOP


def test_goal_bias_breaks_a_tie_towards_the_goal() -> None:
    """With equally open sides, the rover turns towards the goal's side."""
    controller = Controller(safety_distance=1.5)

    assert controller.update(OPEN, corridor=1.0, goal_heading=-0.5) == MotionState.TURN_RIGHT


def test_forward_steering_only_towards_a_clear_goal_direction() -> None:
    """Steer towards the goal when its sector is clear, otherwise keep straight."""
    controller = Controller(safety_distance=1.5, max_forward_turn_deg=15.0)
    blocked_left = OPEN.copy()
    blocked_left[6] = 1.0

    assert np.isclose(controller.forward_steering(OPEN, 0.6), np.deg2rad(15.0))
    assert controller.forward_steering(blocked_left, 0.6) == 0.0
