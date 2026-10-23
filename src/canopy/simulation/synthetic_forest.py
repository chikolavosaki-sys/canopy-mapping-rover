"""Deterministic synthetic forest data for tests and demonstrations."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

PointCloud = NDArray[np.float64]


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

    beam_count: int = 16
    vertical_fov_deg: float = 30.0
    horizontal_samples: int = 180
    max_range_m: float = 30.0
    range_noise_std_m: float = 0.01


def make_forest(
    seed: int,
    plot_size_m: float = 50.0,
    n_trees: int = 40,
    points_per_tree: int = 180,
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
        crown = _make_crown(rng, tree, max(30, points_per_tree // 3))
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
    grid = np.linspace(0, size, max(12, int(size / 2)))
    x, y = np.meshgrid(grid, grid)
    z = 0.08 * np.sin(x / 4) + 0.06 * np.cos(y / 5) + 0.12 * x / size
    return np.column_stack((x.ravel(), y.ravel(), z.ravel()))


def _random_tree(rng: np.random.Generator, size: float) -> Tree:
    return Tree(
        float(rng.uniform(2, size - 2)),
        float(rng.uniform(2, size - 2)),
        float(rng.uniform(0.10, 0.60)),
        float(rng.uniform(8, 20)),
    )


def _make_stem(rng: np.random.Generator, tree: Tree, count: int) -> PointCloud:
    angles = rng.uniform(0, 2 * np.pi, count)
    heights = rng.uniform(0, tree.height * 0.72, count)
    radius = tree.dbh / 2 + rng.normal(0, 0.01, count)
    return np.column_stack(
        (tree.x + radius * np.cos(angles), tree.y + radius * np.sin(angles), heights)
    )


def _make_crown(rng: np.random.Generator, tree: Tree, count: int) -> PointCloud:
    centre = np.array([tree.x, tree.y, tree.height * 0.78])
    spread = np.array([tree.height * 0.20, tree.height * 0.20, tree.height * 0.14])
    return centre + rng.normal(size=(count, 3)) * spread


def _make_shrubs(
    rng: np.random.Generator, size: float
) -> tuple[list[ShrubVolume], PointCloud]:
    shrubs, clouds = [], []
    for _ in range(max(2, int(size / 15))):
        minimum = np.array([rng.uniform(1, size - 3), rng.uniform(1, size - 3), 0.5])
        maximum = minimum + [rng.uniform(1, 3), rng.uniform(1, 3), rng.uniform(0.5, 3.5)]
        shrubs.append(ShrubVolume(tuple(minimum), tuple(maximum)))
        clouds.append(rng.uniform(minimum, maximum, size=(70, 3)))
    return shrubs, np.vstack(clouds)


def _make_rocks(rng: np.random.Generator, size: float) -> PointCloud:
    centres = rng.uniform(1, size - 1, size=(3, 2))
    offsets = rng.normal(0, 0.3, size=(90, 3))
    offsets[:, 2] = np.abs(offsets[:, 2])
    base = np.column_stack(
        (np.repeat(centres[:, 0], 30), np.repeat(centres[:, 1], 30), np.zeros(90))
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
