"""Deterministic synthetic forest data for tests and demonstrations."""

from dataclasses import dataclass

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


@dataclass
class Forest:
    """Synthetic forest points and their semantic labels."""

    points: PointCloud
    labels: NDArray[np.str_]
    trees: list[Tree]
    shrubs: list[ShrubVolume]
    plot_size_m: float


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
    rocks = _make_rocks(rng, plot_size_m)
    points.append(rocks)
    labels.append(np.full(len(rocks), "rock"))
    return Forest(np.vstack(points), np.concatenate(labels), trees, shrubs, plot_size_m)


def simulate_scan(
    forest: Forest,
    pose: np.ndarray,
    sensor: Sensor = Sensor(),
    seed: int = 0,
) -> PointCloud:
    """Sample nearest forest points in angular LiDAR bins, naturally occluding rear points."""
    if pose.shape != (4, 4) or sensor.beam_count < 1 or sensor.horizontal_samples < 1:
        raise ValueError("pose must be 4x4 and sensor sample counts must be positive")
    rng = np.random.default_rng(seed)
    relative = _world_to_sensor(forest.points, pose)
    distances = np.linalg.norm(relative, axis=1)
    azimuth = np.arctan2(relative[:, 1], relative[:, 0])
    elevation = np.arctan2(relative[:, 2], np.maximum(distances, 1e-9))
    bins = _scan_bins(sensor)
    selected: list[np.ndarray] = []
    for azimuth_bin, elevation_bin in bins:
        mask = (
            (np.abs(_angle_difference(azimuth, azimuth_bin)) <= np.pi / sensor.horizontal_samples)
            & (
                np.abs(elevation - elevation_bin)
                <= np.deg2rad(sensor.vertical_fov_deg) / sensor.beam_count
            )
            & (distances <= sensor.max_range_m)
        )
        indices = np.flatnonzero(mask)
        if len(indices):
            selected.append(indices[np.argmin(distances[indices])])
    if not selected:
        return np.empty((0, 3), dtype=np.float64)
    result = relative[np.asarray(selected)]
    result += rng.normal(0.0, sensor.range_noise_std_m, result.shape)
    return _sensor_to_world(result, pose)


def simulate_traversal(
    forest: Forest, waypoints: list[np.ndarray], sensor: Sensor = Sensor()
) -> list[tuple[np.ndarray, PointCloud]]:
    """Return exact poses and scans at each waypoint."""
    return [
        (pose, simulate_scan(forest, pose, sensor, seed=index))
        for index, pose in enumerate(waypoints)
    ]


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


def _make_rocks(rng: np.random.Generator, size: float) -> PointCloud:
    cfg = _SIM["rocks"]
    count, per_rock = cfg["count"], cfg["points_per_rock"]
    margin = cfg["edge_margin_m"]
    centres = rng.uniform(margin, size - margin, size=(count, 2))
    offsets = rng.normal(0, cfg["spread_std_m"], size=(count * per_rock, 3))
    offsets[:, 2] = np.abs(offsets[:, 2])
    base = np.column_stack(
        (
            np.repeat(centres[:, 0], per_rock),
            np.repeat(centres[:, 1], per_rock),
            np.zeros(count * per_rock),
        )
    )
    return base + offsets


def _scan_bins(sensor: Sensor) -> list[tuple[float, float]]:
    azimuths = np.linspace(-np.pi, np.pi, sensor.horizontal_samples, endpoint=False)
    half_fov = np.deg2rad(sensor.vertical_fov_deg) / 2
    elevations = np.linspace(-half_fov, half_fov, sensor.beam_count)
    return [(azimuth, elevation) for elevation in elevations for azimuth in azimuths]


def _world_to_sensor(points: PointCloud, pose: np.ndarray) -> PointCloud:
    return (np.linalg.inv(pose) @ np.column_stack((points, np.ones(len(points)))).T).T[:, :3]


def _sensor_to_world(points: PointCloud, pose: np.ndarray) -> PointCloud:
    return (pose @ np.column_stack((points, np.ones(len(points)))).T).T[:, :3]


def _angle_difference(values: np.ndarray, target: float) -> np.ndarray:
    return np.arctan2(np.sin(values - target), np.cos(values - target))
