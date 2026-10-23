"""Deterministic synthetic forest for tests and demonstrations.

A forest is sloped, bumpy ground plus trees (vertical trunks and crowns),
shrubs, and rocks. Everything has exact ground truth (positions, DBH, shrub
volumes, rock sizes) so the analytics and navigation can be scored. The
simulated LiDAR that scans it lives in ``canopy.simulation.lidar``.
"""

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from canopy.config import section

PointCloud = NDArray[np.float64]
_SIM = section("simulation")


@dataclass(frozen=True)
class Tree:
    """Ground-truth tree: trunk centre, diameter at breast height, total height."""

    x: float
    y: float
    dbh: float
    height: float


@dataclass(frozen=True)
class ShrubVolume:
    """Low-vegetation box: x and y are map coordinates, z is height above ground."""

    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]


@dataclass(frozen=True)
class Rock:
    """Ground-truth boulder: a hemisphere of this radius sitting on the ground."""

    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class Terrain:
    """Ground height = a tilted plane plus a few smooth sine bumps.

    ``waves`` holds ``(amplitude_m, kx, ky, phase)`` per bump. The defaults
    give flat ground at z = 0.
    """

    slope_deg: float = 0.0
    slope_direction: float = 0.0
    waves: tuple[tuple[float, float, float, float], ...] = ()

    def height(self, x: np.ndarray | float, y: np.ndarray | float) -> np.ndarray:
        """Ground height (m) at map coordinates ``x``, ``y``."""
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        along = np.cos(self.slope_direction) * x + np.sin(self.slope_direction) * y
        z = np.tan(np.deg2rad(self.slope_deg)) * along
        for amplitude, kx, ky, phase in self.waves:
            z = z + amplitude * np.sin(kx * x + ky * y + phase)
        return z


@dataclass
class Forest:
    """Synthetic forest points, their semantic labels, and the ground truth."""

    points: PointCloud
    labels: NDArray[np.str_]
    trees: list[Tree]
    shrubs: list[ShrubVolume]
    plot_size_m: float
    rocks: list[Rock] = field(default_factory=list)
    terrain: Terrain = field(default_factory=Terrain)
    cache: dict = field(default_factory=dict, repr=False, compare=False)


def make_forest(
    seed: int,
    plot_size_m: float = _SIM["plot_size_m"],
    n_trees: int = _SIM["tree_count"],
    points_per_tree: int = _SIM["points_per_tree"],
    slope_deg: float | None = None,
) -> Forest:
    """Create a reproducible labelled forest; ``slope_deg=None`` picks a random slope."""
    if plot_size_m <= 0 or n_trees < 1 or points_per_tree < 8:
        raise ValueError("plot_size_m must be positive and point counts must be valid")
    rng = np.random.default_rng(seed)
    terrain = _random_terrain(rng, slope_deg)
    ground = _make_ground(rng, plot_size_m, terrain)
    points, labels, trees = [ground], [np.full(len(ground), "ground")], []
    for _ in range(n_trees):
        tree = _random_tree(rng, plot_size_m)
        base = float(terrain.height(tree.x, tree.y))
        stem = _make_stem(rng, tree, points_per_tree, base)
        crown = _make_crown(rng, tree, _crown_count(points_per_tree), base)
        points.extend((stem, crown))
        labels.extend((np.full(len(stem), "stem"), np.full(len(crown), "crown")))
        trees.append(tree)
    shrubs, shrub_points = _make_shrubs(rng, plot_size_m, terrain)
    rocks, rock_points = _make_rocks(rng, plot_size_m, terrain)
    points.extend((shrub_points, rock_points))
    labels.extend((np.full(len(shrub_points), "shrub"), np.full(len(rock_points), "rock")))
    return Forest(
        np.vstack(points), np.concatenate(labels), trees, shrubs, plot_size_m, rocks, terrain
    )


def traversal_poses(
    forest: Forest, length_m: float | None = None, step_m: float | None = None
) -> list[np.ndarray]:
    """Return sensor poses along a gentle S-shaped path across the plot middle.

    The path starts ``edge_margin_m`` inside the plot and runs ``length_m``
    along x (default: to the far margin), one pose about every ``step_m``.
    The sensor faces along the path, ``sensor_height_m`` above the local ground.
    """
    cfg = _SIM["traversal"]
    margin, size = cfg["edge_margin_m"], forest.plot_size_m
    length = size - 2 * margin if length_m is None else length_m
    step = cfg["step_m"] if step_m is None else step_m
    x = np.linspace(margin, margin + length, int(round(length / step)) + 1)
    y = size / 2 + cfg["sway_amplitude_m"] * np.sin(x / cfg["sway_wavelength_m"])
    z = forest.terrain.height(x, y) + cfg["sensor_height_m"]
    yaw = np.arctan2(np.gradient(y), np.gradient(x))
    poses = []
    for px, py, pz, heading in zip(x, y, z, yaw):
        pose = np.eye(4)
        pose[:2, :2] = [[np.cos(heading), -np.sin(heading)], [np.sin(heading), np.cos(heading)]]
        pose[:3, 3] = (px, py, pz)
        poses.append(pose)
    return poses


def _random_terrain(rng: np.random.Generator, slope_deg: float | None) -> Terrain:
    """A random tilt (up to ``max_slope_deg``) plus smooth bumps of random direction."""
    cfg = _SIM["ground"]
    slope = rng.uniform(0, cfg["max_slope_deg"]) if slope_deg is None else slope_deg
    direction = rng.uniform(-np.pi, np.pi)
    amplitude = cfg["wave_amplitude_m"] / max(cfg["wave_count"], 1)
    waves = []
    for _ in range(cfg["wave_count"]):
        wavenumber = 2 * np.pi / rng.uniform(*cfg["wavelength_range_m"])
        angle, phase = rng.uniform(-np.pi, np.pi), rng.uniform(0, 2 * np.pi)
        waves.append(
            (amplitude, wavenumber * np.cos(angle), wavenumber * np.sin(angle), phase)
        )
    return Terrain(float(slope), float(direction), tuple(waves))


def _make_ground(rng: np.random.Generator, size: float, terrain: Terrain) -> PointCloud:
    cfg = _SIM["ground"]
    grid = np.arange(0.0, size + 1e-9, cfg["spacing_m"])
    x, y = (axis.ravel() for axis in np.meshgrid(grid, grid))
    z = terrain.height(x, y) + rng.normal(0, cfg["roughness_std_m"], len(x))
    return np.column_stack((x, y, z))


def _random_tree(rng: np.random.Generator, size: float) -> Tree:
    cfg = _SIM["trees"]
    margin = cfg["edge_margin_m"]
    return Tree(
        float(rng.uniform(margin, size - margin)),
        float(rng.uniform(margin, size - margin)),
        float(rng.uniform(*cfg["dbh_range_m"])),
        float(rng.uniform(*cfg["height_range_m"])),
    )


def _make_stem(rng: np.random.Generator, tree: Tree, count: int, base: float) -> PointCloud:
    cfg = _SIM["trees"]
    angles = rng.uniform(0, 2 * np.pi, count)
    heights = rng.uniform(0, tree.height * cfg["stem_height_fraction"], count)
    radius = tree.dbh / 2 + rng.normal(0, cfg["bark_noise_std_m"], count)
    return np.column_stack(
        (tree.x + radius * np.cos(angles), tree.y + radius * np.sin(angles), base + heights)
    )


def _crown_count(points_per_tree: int) -> int:
    cfg = _SIM["trees"]
    return max(cfg["crown_min_points"], points_per_tree // cfg["crown_points_divisor"])


def _make_crown(rng: np.random.Generator, tree: Tree, count: int, base: float) -> PointCloud:
    cfg = _SIM["trees"]
    centre = np.array([tree.x, tree.y, base + tree.height * cfg["crown_centre_fraction"]])
    spread = tree.height * np.array(cfg["crown_spread_fraction"])
    return centre + rng.normal(size=(count, 3)) * spread


def _make_shrubs(
    rng: np.random.Generator, size: float, terrain: Terrain
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
        cloud = rng.uniform(minimum, maximum, size=(cfg["points_per_shrub"], 3))
        cloud[:, 2] += terrain.height(cloud[:, 0], cloud[:, 1])  # heights above local ground
        clouds.append(cloud)
    return shrubs, np.vstack(clouds)


def _make_rocks(
    rng: np.random.Generator, size: float, terrain: Terrain
) -> tuple[list[Rock], PointCloud]:
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
    surface[:, :, 2] += terrain.height(centres[:, 0], centres[:, 1])[:, None]
    rocks = [Rock(float(x), float(y), float(r)) for (x, y), r in zip(centres, radii)]
    return rocks, surface.reshape(-1, 3)
