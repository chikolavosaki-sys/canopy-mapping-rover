"""Tests for simulator rover collisions and motion."""

import numpy as np

from canopy.navigation import Controller
from canopy.simulation.rover_sim import run_rover
from canopy.simulation.synthetic_forest import Forest


def test_rover_reports_a_stem_collision() -> None:
    """A stem directly on the path stops the run as a collision."""
    forest = Forest(
        points=np.array([[2.0, 0.0, 0.0], [2.0, 0.0, 1.0]]),
        labels=np.array(["ground", "stem"]),
        trees=[],
        shrubs=[],
        plot_size_m=10.0,
    )
    start = np.eye(4)
    result = run_rover(forest, start, [4.0, 0.0, 0.0], Controller(), max_steps=20)

    assert result.collision
    assert not result.reached_goal
