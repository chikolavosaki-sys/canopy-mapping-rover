"""Simulated spinning LiDAR that ray-casts against the synthetic forest.

The forest is turned into triangle meshes once (ground surface, trunk
cylinders, rock spheres, and crowns/shrubs as clusters of small "leaf clump"
spheres, so foliage is porous). Each scan fires ``beam_count x
horizontal_samples`` rays from the sensor; Open3D's ``RaycastingScene``
returns the first surface each ray hits, so anything behind a trunk is
hidden (true occlusion). Gaussian noise is added along each ray, like real
range noise. Every returned point also gets the label of what it hit.
"""

from dataclasses import dataclass

import numpy as np

from canopy.config import section

from .synthetic_forest import Forest, PointCloud

_SENSOR = section("sensor")
_SIM = section("simulation")
_MESH = _SIM["mesh"]


@dataclass(frozen=True)
class Sensor:
    """Spinning LiDAR settings (defaults roughly match a Velodyne VLP-16)."""

    beam_count: int = _SENSOR["beam_count"]
    vertical_fov_deg: float = _SENSOR["vertical_fov_deg"]
    horizontal_samples: int = _SENSOR["horizontal_samples"]
    max_range_m: float = _SENSOR["max_range_m"]
    range_noise_std_m: float = _SENSOR["range_noise_std_m"]


def simulate_scan(
    forest: Forest, pose: np.ndarray, sensor: Sensor = Sensor(), seed: int = 0
) -> PointCloud:
    """Return one scan's hit points in world coordinates."""
    return scan_with_labels(forest, pose, sensor, seed)[0]


def scan_with_labels(
    forest: Forest, pose: np.ndarray, sensor: Sensor = Sensor(), seed: int = 0
) -> tuple[PointCloud, np.ndarray]:
    """Return world-frame hit points and the label ("ground", "stem", ...) of each."""
    import open3d as o3d

    if pose.shape != (4, 4) or sensor.beam_count < 1 or sensor.horizontal_samples < 1:
        raise ValueError("pose must be 4x4 and sensor sample counts must be positive")
    scene, names = _scene(forest)
    directions = _beam_directions(sensor) @ pose[:3, :3].T
    origin = np.broadcast_to(pose[:3, 3], directions.shape)
    rays = o3d.core.Tensor(np.hstack((origin, directions)), dtype=o3d.core.Dtype.Float32)
    hits = scene.cast_rays(rays)
    distance = hits["t_hit"].numpy().astype(np.float64)
    keep = np.isfinite(distance) & (distance <= sensor.max_range_m)
    rng = np.random.default_rng(seed)
    noisy = distance[keep] + rng.normal(0.0, sensor.range_noise_std_m, int(keep.sum()))
    points = pose[:3, 3] + directions[keep] * noisy[:, None]
    labels = np.asarray(names)[hits["geometry_ids"].numpy()[keep].astype(np.int64)]
    return points, labels


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
        sequence.append((pose, to_sensor_frame(scan, pose) if sensor_frame else scan))
    return sequence


def to_sensor_frame(points: PointCloud, pose: np.ndarray) -> PointCloud:
    """Express world points relative to a sensor pose."""
    homogeneous = np.column_stack((points, np.ones(len(points))))
    return (np.linalg.inv(pose) @ homogeneous.T).T[:, :3]


def _beam_directions(sensor: Sensor) -> np.ndarray:
    """Unit ray directions in the sensor frame, ring by ring (+x forward, +z up)."""
    half_fov = np.deg2rad(sensor.vertical_fov_deg) / 2
    elevation = np.linspace(-half_fov, half_fov, sensor.beam_count)
    azimuth = np.linspace(-np.pi, np.pi, sensor.horizontal_samples, endpoint=False)
    el, az = (grid.ravel() for grid in np.meshgrid(elevation, azimuth, indexing="ij"))
    return np.column_stack((np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)))


def _scene(forest: Forest) -> tuple[object, list[str]]:
    """Build (once per forest) the ray-casting scene and the label of each geometry."""
    if "scene" not in forest.cache:
        import open3d as o3d

        scene, names = o3d.t.geometry.RaycastingScene(), []
        for name, (vertices, triangles) in _meshes(forest).items():
            if len(triangles):
                mesh = o3d.t.geometry.TriangleMesh()
                mesh.vertex.positions = o3d.core.Tensor(vertices, dtype=o3d.core.Dtype.Float32)
                mesh.triangle.indices = o3d.core.Tensor(triangles, dtype=o3d.core.Dtype.Int32)
                scene.add_triangles(mesh)  # geometry ids are 0, 1, 2, ... in this order
                names.append(name)
        forest.cache["scene"] = (scene, names)
    return forest.cache["scene"]


def _meshes(forest: Forest) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Vertices and triangles for each labelled part of the forest."""
    base = forest.terrain.height
    rocks = _copies(
        _unit_sphere(),
        np.array([[r.x, r.y, float(base(r.x, r.y))] for r in forest.rocks]),
        np.array([[r.radius] * 3 for r in forest.rocks]),
    )
    return {
        "ground": _ground_mesh(forest),
        "stem": _trunks(forest),
        "crown": _clumps(forest, "crown", _MESH["crown_clump_radius_m"]),
        "shrub": _clumps(forest, "shrub", _MESH["shrub_clump_radius_m"]),
        "rock": rocks,
    }


def _trunks(forest: Forest) -> tuple[np.ndarray, np.ndarray]:
    """Vertical cylinders from just below the ground to the top of each stem."""
    if not forest.trees:
        return np.empty((0, 3)), np.empty((0, 3), dtype=np.int64)
    x, y, dbh, height = np.array([[t.x, t.y, t.dbh, t.height] for t in forest.trees]).T
    bottom = forest.terrain.height(x, y) - _MESH["trunk_sink_m"]
    top = forest.terrain.height(x, y) + height * _SIM["trees"]["stem_height_fraction"]
    centres = np.column_stack((x, y, (bottom + top) / 2))
    scales = np.column_stack((dbh / 2, dbh / 2, top - bottom))
    return _copies(_unit_cylinder(), centres, scales)


def _clumps(forest: Forest, label: str, radius: float) -> tuple[np.ndarray, np.ndarray]:
    """One small sphere per labelled point: porous foliage."""
    centres = forest.points[forest.labels == label]
    return _copies(_unit_sphere(), centres, np.full((len(centres), 3), radius))


def _ground_mesh(forest: Forest) -> tuple[np.ndarray, np.ndarray]:
    """Triangulated ground surface covering the plot.

    When the forest's ground points form the full sample grid (as from
    ``make_forest``), they are the mesh vertices, so rays hit the same rough
    surface as the perfect cloud. Otherwise the smooth terrain is used.
    """
    grid = np.arange(0.0, forest.plot_size_m + 1e-9, _SIM["ground"]["spacing_m"])
    n = len(grid)
    vertices = forest.points[forest.labels == "ground"]
    if len(vertices) != n * n:
        x, y = (axis.ravel() for axis in np.meshgrid(grid, grid))
        vertices = np.column_stack((x, y, forest.terrain.height(x, y)))
    i, j = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing="ij")
    corner = (i * n + j).ravel()
    triangles = np.vstack(
        (
            np.column_stack((corner, corner + n, corner + 1)),
            np.column_stack((corner + 1, corner + n, corner + n + 1)),
        )
    )
    return vertices, triangles


def _copies(
    template: tuple[np.ndarray, np.ndarray], centres: np.ndarray, scales: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Scale and move one template mesh to many places, as a single mesh."""
    vertices, triangles = template
    if not len(centres):
        return np.empty((0, 3)), np.empty((0, 3), dtype=np.int64)
    moved = centres[:, None, :] + scales[:, None, :] * vertices[None, :, :]
    offsets = np.arange(len(centres))[:, None, None] * len(vertices)
    return moved.reshape(-1, 3), (triangles[None, :, :] + offsets).reshape(-1, 3)


def _unit_cylinder() -> tuple[np.ndarray, np.ndarray]:
    """Radius-1, height-1 cylinder centred on the origin."""
    import open3d as o3d

    mesh = o3d.geometry.TriangleMesh.create_cylinder(1.0, 1.0, _MESH["cylinder_resolution"])
    return np.asarray(mesh.vertices), np.asarray(mesh.triangles)


def _unit_sphere() -> tuple[np.ndarray, np.ndarray]:
    """Radius-1 sphere centred on the origin."""
    import open3d as o3d

    mesh = o3d.geometry.TriangleMesh.create_sphere(1.0, _MESH["sphere_resolution"])
    return np.asarray(mesh.vertices), np.asarray(mesh.triangles)
