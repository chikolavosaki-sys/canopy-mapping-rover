"""Tests for the synthetic forest and the ray-casting LiDAR."""

import numpy as np

from canopy.simulation.lidar import Sensor, _beam_directions, scan_with_labels
from canopy.simulation.synthetic_forest import Forest, Terrain, Tree, make_forest


def test_forest_generation_is_reproducible_and_labelled() -> None:
    """The same seed creates identical points and semantic labels."""
    first = make_forest(seed=7, plot_size_m=20, n_trees=4)
    second = make_forest(seed=7, plot_size_m=20, n_trees=4)

    np.testing.assert_allclose(first.points, second.points)
    np.testing.assert_array_equal(first.labels, second.labels)
    assert set(first.labels) == {"ground", "stem", "crown", "shrub", "rock"}
    assert len(first.trees) == 4


def test_label_counts_are_sane() -> None:
    """Ground dominates, every tree has stem points, and each class is present."""
    forest = make_forest(seed=2, plot_size_m=20, n_trees=5, points_per_tree=200)
    counts = {name: int((forest.labels == name).sum()) for name in set(forest.labels)}

    assert counts["ground"] > counts["shrub"] > 0
    assert counts["stem"] == 5 * 200
    assert counts["rock"] > 0 and counts["crown"] > 0


def test_slope_follows_the_requested_angle() -> None:
    """A 15 degree forest's ground rises about tan(15 deg) per metre along the slope."""
    forest = make_forest(seed=1, plot_size_m=30, n_trees=3, slope_deg=15.0)
    terrain = forest.terrain
    direction = np.array([np.cos(terrain.slope_direction), np.sin(terrain.slope_direction)])
    rise = terrain.height(*(direction * 10)) - terrain.height(0.0, 0.0)

    assert abs(rise - 10 * np.tan(np.deg2rad(15))) < 0.3  # bumps add at most +-0.3 m


def test_trees_and_shrubs_stand_on_the_sloped_ground() -> None:
    """Stem points start at the local ground, not at z = 0."""
    forest = make_forest(seed=4, plot_size_m=30, n_trees=3, slope_deg=12.0)
    stems = forest.points[forest.labels == "stem"]
    for tree in forest.trees:
        own = stems[np.hypot(stems[:, 0] - tree.x, stems[:, 1] - tree.y) < tree.dbh]
        assert abs(own[:, 2].min() - forest.terrain.height(tree.x, tree.y)) < 0.2


def test_beam_directions_are_unit_vectors_within_the_fov() -> None:
    """Every ray is a unit vector, spanning exactly the vertical field of view."""
    directions = _beam_directions(Sensor(beam_count=16, vertical_fov_deg=30.0))
    elevation = np.degrees(np.arcsin(directions[:, 2]))

    np.testing.assert_allclose(np.linalg.norm(directions, axis=1), 1.0)
    assert np.isclose(elevation.min(), -15.0) and np.isclose(elevation.max(), 15.0)


def test_nearer_trunk_occludes_the_trunk_behind_it() -> None:
    """Rays straight ahead stop on the front trunk; the one behind is hidden."""
    forest = Forest(
        points=np.zeros((1, 3)),
        labels=np.array(["ground"]),
        trees=[Tree(3.0, 0.0, 0.4, 10.0), Tree(6.0, 0.0, 0.4, 10.0)],
        shrubs=[],
        plot_size_m=20.0,
        terrain=Terrain(),
    )
    pose = np.eye(4)
    pose[2, 3] = 1.0

    points, labels = scan_with_labels(forest, pose, Sensor(range_noise_std_m=0.0))
    ahead = points[(np.abs(points[:, 1]) < 0.1) & (points[:, 0] > 0) & (labels == "stem")]

    assert len(ahead) > 0
    np.testing.assert_allclose(ahead[:, 0], 2.8, atol=0.05)


def test_rocks_are_solid_hemispheres() -> None:
    """Rock points lie on the surface the rover can collide with."""
    forest = make_forest(seed=1, plot_size_m=20, n_trees=2)
    rock_points = forest.points[forest.labels == "rock"]
    per_rock = len(rock_points) // len(forest.rocks)

    for index, rock in enumerate(forest.rocks):
        points = rock_points[index * per_rock : (index + 1) * per_rock]
        centre = [rock.x, rock.y, float(forest.terrain.height(rock.x, rock.y))]
        np.testing.assert_allclose(np.linalg.norm(points - centre, axis=1), rock.radius)


def test_rays_hit_the_same_rough_ground_as_the_ground_points() -> None:
    """The ray-cast ground is the forest's own rough ground points, not a smooth surface."""
    forest = make_forest(seed=5, plot_size_m=10, n_trees=1)
    ground = forest.points[forest.labels == "ground"]
    target = ground[np.argmin(np.hypot(ground[:, 0] - 4.0, ground[:, 1] - 6.0))]
    pose = np.eye(4)
    pose[:3, :3] = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]  # sensor x axis points straight down
    pose[:3, 3] = (target[0], target[1], target[2] + 2.0)

    straight_down = Sensor(beam_count=1, vertical_fov_deg=0.0, range_noise_std_m=0.0)
    points, labels = scan_with_labels(forest, pose, straight_down)
    below = points[(labels == "ground") & (np.hypot(*(points[:, :2] - target[:2]).T) < 0.01)]

    assert len(below) > 0
    np.testing.assert_allclose(below[:, 2], target[2], atol=1e-4)
