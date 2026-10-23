"""Tests for simulator rover motion, avoidance, and collisions."""

import numpy as np

from canopy.navigation import Controller
from canopy.simulation.rover_sim import collides, run_rover
from canopy.simulation.synthetic_forest import Forest, Rock, Tree


def _forest_with_tree_at(x: float, y: float, dbh: float = 0.4) -> Forest:
    """One trunk drawn as a dense ring of points from 0 to 3 m height, flat ground."""
    angles = np.linspace(0, 2 * np.pi, 72, endpoint=False)
    heights = np.linspace(0.0, 3.0, 31)
    trunk = np.array(
        [[x + dbh / 2 * np.cos(a), y + dbh / 2 * np.sin(a), h] for h in heights for a in angles]
    )
    ground = np.array([[gx, gy, 0.0] for gx in range(11) for gy in range(11)], dtype=float)
    return Forest(
        points=np.vstack((ground, trunk)),
        labels=np.array(["ground"] * len(ground) + ["stem"] * len(trunk)),
        trees=[Tree(x, y, dbh, 10.0)],
        shrubs=[],
        plot_size_m=10.0,
    )


def test_rover_drives_around_a_tree_on_the_straight_line() -> None:
    """A trunk exactly between start and goal is avoided and the goal is reached."""
    forest = _forest_with_tree_at(5.0, 5.0)
    start = np.eye(4)
    start[:2, 3] = (1.0, 5.0)

    result = run_rover(forest, start, np.array([9.0, 5.0]), Controller())

    assert result.reached_goal and not result.collision
    path = np.array([pose[:2, 3] for pose in result.poses])
    assert np.max(np.abs(path[:, 1] - 5.0)) > 0.3  # it left the straight line
    assert np.min(np.linalg.norm(path - [5.0, 5.0], axis=1)) > 0.2 + 0.35  # never touched


def test_collision_uses_trunk_and_rock_geometry() -> None:
    """Footprint vs trunk radius; rocks count only above the rover's ground clearance."""
    forest = Forest(
        points=np.zeros((1, 3)),
        labels=np.array(["ground"]),
        trees=[Tree(0.0, 0.0, 0.4, 10.0)],
        shrubs=[],
        plot_size_m=10.0,
        rocks=[Rock(5.0, 0.0, 0.5), Rock(8.0, 0.0, 0.25)],
    )

    assert collides(np.array([0.5, 0.0]), forest, rover_radius=0.35)  # 0.5 < 0.2 + 0.35
    assert not collides(np.array([0.6, 0.0]), forest, rover_radius=0.35)
    assert collides(np.array([5.7, 0.0]), forest, rover_radius=0.35)  # sqrt(.5^2-.3^2) = 0.4
    assert not collides(np.array([8.0, 0.0]), forest, rover_radius=0.35)  # lower than clearance
