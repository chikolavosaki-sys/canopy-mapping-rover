"""Small point-cloud file and geometry helpers."""

from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray

Points = NDArray[np.float64]


def _validate_points(points: ArrayLike) -> Points:
    """Convert points to a finite float64 ``(N, 3)`` array."""
    result = np.asarray(points, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    if not np.all(np.isfinite(result)):
        raise ValueError("points must contain only finite values")
    return result


def load_points(path: str | Path) -> Points:
    """Load XYZ coordinates from NPY, text, PLY, PCD, LAS, or LAZ."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".npy":
        return _validate_points(np.load(source))
    if suffix in {".txt", ".xyz"}:
        return _validate_points(np.loadtxt(source, usecols=(0, 1, 2)))
    if suffix in {".ply", ".pcd"}:
        import open3d as o3d

        cloud = o3d.io.read_point_cloud(str(source))
        return _validate_points(np.asarray(cloud.points))
    if suffix in {".las", ".laz"}:
        import laspy

        las = laspy.read(source)
        return _validate_points(np.column_stack((las.x, las.y, las.z)))
    raise ValueError(f"unsupported point-cloud extension: {suffix}")


def save_points(points: ArrayLike, path: str | Path) -> None:
    """Save XYZ coordinates to NPY, PLY, or LAZ."""
    values = _validate_points(points)
    destination = Path(path)
    suffix = destination.suffix.lower()
    if suffix == ".npy":
        np.save(destination, values)
        return
    if suffix == ".ply":
        import open3d as o3d

        cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(values))
        if not o3d.io.write_point_cloud(str(destination), cloud):
            raise OSError(f"could not write {destination}")
        return
    if suffix == ".laz":
        import laspy

        header = laspy.LasHeader(point_format=3, version="1.2")
        las = laspy.LasData(header)
        las.x, las.y, las.z = values.T
        las.write(destination)
        return
    raise ValueError("save_points supports only .npy, .ply, and .laz")


def voxel_downsample(points: ArrayLike, voxel_size: float) -> Points:
    """Keep one representative point per occupied voxel."""
    values = _validate_points(points)
    if voxel_size <= 0:
        raise ValueError("voxel_size must be positive")
    keys = np.floor(values / voxel_size).astype(np.int64)
    _, indices = np.unique(keys, axis=0, return_index=True)
    return values[np.sort(indices)]


def crop_box(points: ArrayLike, minimum: ArrayLike, maximum: ArrayLike) -> Points:
    """Return points inside an axis-aligned inclusive box."""
    values = _validate_points(points)
    lower, upper = np.asarray(minimum, dtype=float), np.asarray(maximum, dtype=float)
    if lower.shape != (3,) or upper.shape != (3,) or np.any(lower > upper):
        raise ValueError("minimum and maximum must be valid 3D bounds")
    mask = np.all((values >= lower) & (values <= upper), axis=1)
    return values[mask]


def crop_radius(points: ArrayLike, centre: ArrayLike, radius: float) -> Points:
    """Return points within a 3D radius of a centre."""
    values = _validate_points(points)
    origin = np.asarray(centre, dtype=float)
    if origin.shape != (3,) or radius < 0:
        raise ValueError("centre must be 3D and radius must be non-negative")
    return values[np.sum((values - origin) ** 2, axis=1) <= radius**2]
