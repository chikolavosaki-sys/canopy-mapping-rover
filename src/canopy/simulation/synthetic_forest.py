"""Deterministic synthetic forest data for tests and demonstrations."""

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from canopy.config import section

PointCloud = NDArray[np.float64]
_SIM = section("simulation")
_SENSOR = section("sensor")


@dataclass(frozen=True)
class Tree:
    """Ground-truth tree geometry."""

    x: float
    y: float
    dbh: float
    height: float


@dataclass(frozen=True)
class ShrubVolume:
    """Axis-aligned low-vegetation volume."""

    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]


@dataclass(frozen=True)
class Rock:
    """Ground-truth rock: a solid disc the rover must not drive into."""

    x: float
    y: float
    radius: float


@dataclass
class Forest:
    """Synthetic forest points and their semantic labels."""

    points: PointCloud
    labels: NDArray[np.str_]
    trees: list[Tree]
    shrubs: list[ShrubVolume]
    plot_size_m: float
    rocks: list[Rock] = field(default_factory=list)


@dataclass(frozen=True)
class Sensor:
    """Simple spinning LiDAR settings."""

    beam_count: int = _SENSOR["beam_count"]
    vertical_fov_deg: float = _SENSOR["vertical_fov_deg"]
    horizontal_samples: int = _SENSOR["horizontal_samples"]
    max_range_m: float = _SENSOR["max_range_m"]
    range_noise_std_m: float = _SENSOR["range_noise_std_m"]


def make_forest(
    seed: int,
    plot_size_m: float = _SIM["plot_size_m"],
    n_trees: int = _SIM["tree_count"],
    points_per_tree: int = _SIM["points_per_tree"],
) -> Forest:
    """Create a reproducible labelled forest with uneven ground and obstacles."""
    if plot_size_m <= 0 or n_trees < 1 or points_per_tree < 8:
        raise ValueError("plot_size_m must be positive and point counts must be valid")
    rng = np.random.default_rng(seed)
    ground = _make_ground(rng, plot_size_m)
    points, labels, trees = [ground], [np.full(len(ground), "ground")], []
    for _ in range(n_trees):
        tree = _random_tree(rng, plot_size_m)
        stem = _make_stem(rng, tree, points_per_tree)
        crown = _make_crown(rng, tree, _crown_count(points_per_tree))
        points.extend((stem, crown))
        labels.extend((np.full(len(stem), "stem"), np.full(len(crown), "crown")))
        trees.append(tree)
    shrubs, shrub_points = _make_shrubs(rng, plot_size_m)
    points.append(shrub_points)
    labels.append(np.full(len(shrub_points), "shrub"))
    rocks, rock_points = _make_rocks(rng, plot_size_m)
    points.append(rock_points)
    labels.append(np.full(len(rock_points), "rock"))
    return Forest(np.vstack(points), np.concatenate(labels), trees, shrubs, plot_size_m, rocks)


def simulate_scan(
    forest: Forest,
    pose: np.ndarray,
    sensor: Sensor = Sensor(),
    seed: int = 0,
) -> PointCloud:
    """Return the nearest forest point in each beam direction, plus noise (world frame).

    Each of ``beam_count x horizontal_samples`` beams keeps only its closest
    point, so anything behind a trunk is hidden (occlusion). The work is done
    one beam ring at a time with array operations instead of one beam at a time.
    """
    if pose.shape != (4, 4) or sensor.beam_count < 1 or sensor.horizontal_samples < 1:
        raise ValueError("pose must be 4x4 and sensor sample counts must be positive")
    rng = np.random.default_rng(seed)
    relative = _world_to_sensor(forest.points, pose)
    distances = np.linalg.norm(relative, axis=1)
    picks = _nearest_per_beam(relative, distances, sensor)
    if not len(picks):
        return np.empty((0, 3), dtype=np.float64)
    result = relative[picks]
    result += rng.normal(0.0, sensor.range_noise_std_m, result.shape)
    return _sensor_to_world(result, pose)


def _nearest_per_beam(
    relative: PointCloud, distances: np.ndarray, sensor: Sensor
) -> np.ndarray:
    """Indices of the closest point per beam, ordered ring by ring, then by azimuth."""
    azimuth = np.arctan2(relative[:, 1], relative[:, 0])
    elevation = np.arctan2(relative[:, 2], np.maximum(distances, 1e-9))
    step = 2 * np.pi / sensor.horizontal_samples
    azimuth_bin = np.round((azimuth + np.pi) / step).astype(int) % sensor.horizontal_samples
    half_fov = np.deg2rad(sensor.vertical_fov_deg) / 2
    tolerance = np.deg2rad(sensor.vertical_fov_deg) / sensor.beam_count
    in_range = distances <= sensor.max_range_m
    picks = []
    for ring in np.linspace(-half_fov, half_fov, sensor.beam_count):
        candidates = np.flatnonzero(in_range & (np.abs(elevation - ring) <= tolerance))
        # Sort by azimuth bin, then distance; the first entry of each bin is its nearest point.
        ordered = candidates[np.lexsort((distances[candidates], azimuth_bin[candidates]))]
        _, first = np.unique(azimuth_bin[ordered], return_index=True)
        picks.append(ordered[first])
    return np.concatenate(picks) if picks else np.empty(0, dtype=int)


def simulate_traversal(
    forest: Forest,
    waypoints: list[np.ndarray],
    sensor: Sensor = Sensor(),
    sensor_frame: bool = False,
) -> list[tuple[np.ndarray, PointCloud]]:
    """Return exact poses and scans at each waypoint.

    Scans are in world coordinates unless ``sensor_frame`` is true. Use the
    sensor frame for odometry: a real LiDAR only sees points relative to itself.
    """
    sequence = []
    for index, pose in enumerate(waypoints):
        scan = simulate_scan(forest, pose, sensor, seed=index)
        sequence.append((pose, _world_to_sensor(scan, pose) if sensor_frame else scan))
    return sequence


def traversal_poses(
    plot_size_m: float, length_m: float | None = None, step_m: float | None = None
) -> list[np.ndarray]:
    """Return sensor poses along a gentle S-shaped path across the plot middle.

    The path starts ``edge_margin_m`` inside the plot and runs ``length_m``
    along x (default: to the far margin), one pose about every ``step_m``.
    The sensor faces along the path, ``sensor_height_m`` above z = 0.
    """
    cfg = _SIM["traversal"]
    margin = cfg["edge_margin_m"]
    length = plot_size_m - 2 * margin if length_m is None else length_m
    step = cfg["step_m"] if step_m is None else step_m
    x = np.linspace(margin, margin + length, int(round(length / step)) + 1)
    y = plot_size_m / 2 + cfg["sway_amplitude_m"] * np.sin(x / cfg["sway_wavelength_m"])
    yaw = np.arctan2(np.gradient(y), np.gradient(x))
    poses = []
    for px, py, heading in zip(x, y, yaw):
        pose = np.eye(4)
        pose[:2, :2] = [[np.cos(heading), -np.sin(heading)], [np.sin(heading), np.cos(heading)]]
        pose[:3, 3] = (px, py, cfg["sensor_height_m"])
        poses.append(pose)
    return poses


def _make_ground(rng: np.random.Generator, size: float) -> PointCloud:
    cfg = _SIM["ground"]
    grid = np.linspace(0, size, max(cfg["min_points_per_side"], int(size / cfg["spacing_m"])))
    x, y = np.meshgrid(grid, grid)
    (a1, a2), (w1, w2) = cfg["wave_amplitudes_m"], cfg["wave_lengths_m"]
    z = a1 * np.sin(x / w1) + a2 * np.cos(y / w2) + cfg["slope_rise_m"] * x / size
    return np.column_stack((x.ravel(), y.ravel(), z.ravel()))


def _random_tree(rng: np.random.Generator, size: float) -> Tree:
    cfg = _SIM["trees"]
    margin = cfg["edge_margin_m"]
    return Tree(
        float(rng.uniform(margin, size - margin)),
        float(rng.uniform(margin, size - margin)),
        float(rng.uniform(*cfg["dbh_range_m"])),
        float(rng.uniform(*cfg["height_range_m"])),
    )


def _make_stem(rng: np.random.Generator, tree: Tree, count: int) -> PointCloud:
    angles = rng.uniform(0, 2 * np.pi, count)
    cfg = _SIM["trees"]
    heights = rng.uniform(0, tree.height * cfg["stem_height_fraction"], count)
    radius = tree.dbh / 2 + rng.normal(0, cfg["bark_noise_std_m"], count)
    return np.column_stack(
        (tree.x + radius * np.cos(angles), tree.y + radius * np.sin(angles), heights)
    )


def _crown_count(points_per_tree: int) -> int:
    cfg = _SIM["trees"]
    return max(cfg["crown_min_points"], points_per_tree // cfg["crown_points_divisor"])


def _make_crown(rng: np.random.Generator, tree: Tree, count: int) -> PointCloud:
    cfg = _SIM["trees"]
    centre = np.array([tree.x, tree.y, tree.height * cfg["crown_centre_fraction"]])
    spread = tree.height * np.array(cfg["crown_spread_fraction"])
    return centre + rng.normal(size=(count, 3)) * spread


def _make_shrubs(
    rng: np.random.Generator, size: float
) -> tuple[list[ShrubVolume], PointCloud]:
    cfg = _SIM["shrubs"]
    low, high = cfg["edge_margin_m"], size - cfg["footprint_range_m"][1]
    shrubs, clouds = [], []
    for _ in range(max(cfg["min_count"], int(size / cfg["area_per_shrub_m"]))):
        minimum = np.array([rng.uniform(low, high), rng.uniform(low, high), cfg["base_height_m"]])
        maximum = minimum + [
            rng.uniform(*cfg["footprint_range_m"]),
            rng.uniform(*cfg["footprint_range_m"]),
            rng.uniform(*cfg["height_range_m"]),
        ]
        shrubs.append(ShrubVolume(tuple(minimum), tuple(maximum)))
        clouds.append(rng.uniform(minimum, maximum, size=(cfg["points_per_shrub"], 3)))
    return shrubs, np.vstack(clouds)


def _make_rocks(rng: np.random.Generator, size: float) -> tuple[list[Rock], PointCloud]:
    """Boulders as hemispheres: the LiDAR sees the same surface the rover can hit."""
    cfg = _SIM["rocks"]
    count, per_rock = cfg["count"], cfg["points_per_rock"]
    margin = cfg["edge_margin_m"]
    centres = rng.uniform(margin, size - margin, size=(count, 2))
    radii = rng.uniform(*cfg["radius_range_m"], size=count)
    directions = rng.normal(size=(count, per_rock, 3))
    directions /= np.linalg.norm(directions, axis=2, keepdims=True)
    directions[:, :, 2] = np.abs(directions[:, :, 2])  # upper half only
    surface = directions * radii[:, None, None]
    surface[:, :, :2] += centres[:, None, :]
    rocks = [Rock(float(x), float(y), float(r)) for (x, y), r in zip(centres, radii)]
    return rocks, surface.reshape(-1, 3)


def _world_to_sensor(points: PointCloud, pose: np.ndarray) -> PointCloud:
    return (np.linalg.inv(pose) @ np.column_stack((points, np.ones(len(points)))).T).T[:, :3]


def _sensor_to_world(points: PointCloud, pose: np.ndarray) -> PointCloud:
    return (pose @ np.column_stack((points, np.ones(len(points)))).T).T[:, :3]
