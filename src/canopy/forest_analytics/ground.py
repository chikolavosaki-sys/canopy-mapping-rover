"""Ground classification, terrain model (DTM), and height normalisation.

1. Classify ground points with the Cloth Simulation Filter (CSF): turn the
   cloud upside down and drop a virtual cloth onto it; points the cloth comes
   to rest on are ground. Fallback: in each 5 m tile, fit a RANSAC plane to the
   lowest point of every 1 m cell and call points near that plane ground.
2. Build a DTM: the mean ground height in each 1 m cell; empty cells copy the
   nearest filled cell.
3. Height-normalise: subtract the DTM, interpolated between cell centres, so
   every point's z becomes its height above the local ground.
"""

import contextlib
import os
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from canopy.config import section

_GROUND = section("ground")


@dataclass(frozen=True)
class GroundModel:
    """Digital terrain model: ground height at the centre of each XY cell."""

    origin: tuple[float, float]
    resolution: float
    elevations: NDArray[np.float64]

    def height_at(self, xy: ArrayLike) -> NDArray[np.float64]:
        """Ground height under each XY point, interpolated between cell centres."""
        from scipy.interpolate import RegularGridInterpolator

        nx, ny = self.elevations.shape
        centres_x = self.origin[0] + (np.arange(nx) + 0.5) * self.resolution
        centres_y = self.origin[1] + (np.arange(ny) + 0.5) * self.resolution
        if nx < 2 or ny < 2:
            return np.full(len(np.atleast_2d(xy)), float(self.elevations.mean()))
        interpolate = RegularGridInterpolator(
            (centres_x, centres_y), self.elevations, bounds_error=False, fill_value=None
        )
        return interpolate(np.atleast_2d(np.asarray(xy, dtype=float))[:, :2])


def normalize_heights(
    points: ArrayLike,
    method: str = _GROUND["method"],
    resolution: float = _GROUND["grid_size_m"],
) -> tuple[GroundModel, NDArray[np.float64], NDArray[np.bool_]]:
    """Return the DTM, the height-normalised points, and the ground mask."""
    values = _points(points)
    is_ground = classify_ground(values, method)
    model = fit_dtm(values, is_ground, resolution)
    normalized = values.copy()
    normalized[:, 2] -= model.height_at(values)
    return model, normalized, is_ground


def classify_ground(points: ArrayLike, method: str = _GROUND["method"]) -> NDArray[np.bool_]:
    """True for ground points. ``method`` is "csf" or "ransac"; CSF falls back if missing."""
    values = _points(points)
    if method == "csf":
        try:
            return _csf_ground(values)
        except ImportError:
            method = "ransac"
    if method != "ransac":
        raise ValueError(f"unknown ground method {method!r}")
    return _ransac_ground(values)


def fit_dtm(
    points: ArrayLike, is_ground: ArrayLike, resolution: float = _GROUND["grid_size_m"]
) -> GroundModel:
    """Ground height at every cell centre from a local plane fit.

    For each cell, fit ``z = a x + b y + c`` by least squares to the ground
    points in its 3 x 3 neighbourhood and evaluate it at the cell centre. This
    is exact on planar ground wherever the points lie in the cell (a plain
    cell mean is biased on slopes because points rarely sit at the centre).
    Cells without enough nearby ground copy the nearest fitted cell.
    """
    from scipy.ndimage import distance_transform_edt, uniform_filter

    values, mask = _points(points), np.asarray(is_ground, dtype=bool)
    if resolution <= 0 or not mask.any():
        raise ValueError("resolution must be positive and some points must be ground")
    origin = values[:, :2].min(axis=0)
    shape = tuple(np.floor((values[:, :2].max(axis=0) - origin) / resolution).astype(int) + 1)
    local = values[mask] - [*origin, 0.0]  # small coordinates for well-conditioned sums
    cells = np.floor(local[:, :2] / resolution).astype(int)
    x, y, z = local.T
    moments = [np.ones_like(x), x, y, z, x * x, x * y, y * y, x * z, y * z]
    sums = []
    for weight in moments:  # per-cell sums, then summed over each 3 x 3 neighbourhood
        grid = np.zeros(shape)
        np.add.at(grid, (cells[:, 0], cells[:, 1]), weight)
        sums.append(uniform_filter(grid, size=3, mode="constant") * 9)
    n, sx, sy, sz, sxx, sxy, syy, sxz, syz = sums
    normal = np.stack([np.stack([sxx, sxy, sx], -1), np.stack([sxy, syy, sy], -1),
                       np.stack([sx, sy, n], -1)], -2)
    target = np.stack([sxz, syz, sz], -1)
    i, j = np.indices(shape)
    centre_x, centre_y = (i + 0.5) * resolution, (j + 0.5) * resolution
    heights = np.full(shape, np.nan)
    solvable = (n >= 3) & (np.abs(np.linalg.det(normal)) > 1e-9)
    if solvable.any():
        a, b, c = np.linalg.solve(normal[solvable], target[solvable][..., None])[..., 0].T
        heights[solvable] = a * centre_x[solvable] + b * centre_y[solvable] + c
    flat_cells = ~solvable & (n > 0)  # ground present but too few or collinear points
    heights[flat_cells] = sz[flat_cells] / n[flat_cells]
    missing = np.isnan(heights)
    if missing.all():
        raise ValueError("no cell has ground points")
    nearest = distance_transform_edt(missing, return_distances=False, return_indices=True)
    return GroundModel(tuple(origin), resolution, heights[tuple(nearest)])


def lowest_per_cell(points: ArrayLike, cell_size: float) -> NDArray[np.int64]:
    """Indices of the lowest point in each occupied XY cell (likely ground)."""
    values = _points(points)
    cells = np.floor(values[:, :2] / cell_size).astype(np.int64)
    order = np.lexsort((values[:, 2], cells[:, 1], cells[:, 0]))
    _, first = np.unique(cells[order], axis=0, return_index=True)
    return order[first]


def fit_plane_ransac(
    points: ArrayLike, distance: float, iterations: int, seed: int = 0
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Fit ``z = a x + b y + c`` robustly; return ``(a, b, c)`` and the inlier mask.

    RANSAC: try planes through random triples of points, keep the one with the
    most points within ``distance``, then refine it by least squares on those
    inliers. Points on trunks or shrubs do not pull the plane up.
    """
    values = _points(points)
    if len(values) < 3:
        raise ValueError("need at least three points to fit a plane")
    rng = np.random.default_rng(seed)
    design = np.column_stack((values[:, :2], np.ones(len(values))))
    best = np.zeros(len(values), dtype=bool)
    for _ in range(iterations):
        sample = rng.choice(len(values), 3, replace=False)
        try:
            plane = np.linalg.solve(design[sample], values[sample, 2])
        except np.linalg.LinAlgError:
            continue
        inliers = np.abs(design @ plane - values[:, 2]) <= distance
        if inliers.sum() > best.sum():
            best = inliers
    if best.sum() < 3:
        best[:] = True
    plane = np.linalg.lstsq(design[best], values[best, 2], rcond=None)[0]
    return plane, best


def _csf_ground(values: NDArray[np.float64]) -> NDArray[np.bool_]:
    """Cloth Simulation Filter via the ``cloth-simulation-filter`` package (``import CSF``)."""
    import CSF

    cfg = _GROUND["csf"]
    csf = CSF.CSF()
    csf.params.cloth_resolution = cfg["cloth_resolution_m"]
    csf.params.rigidness = cfg["rigidness"]
    csf.params.class_threshold = cfg["class_threshold_m"]
    csf.params.interations = cfg["iterations"]  # sic: the package's own spelling
    csf.params.bSloopSmooth = cfg["slope_smooth"]
    csf.setPointCloud(values)
    ground, non_ground = CSF.VecInt(), CSF.VecInt()
    with _quiet_stdout():  # the C++ library prints progress lines
        csf.do_filtering(ground, non_ground, False)
    mask = np.zeros(len(values), dtype=bool)
    mask[np.asarray(ground, dtype=np.int64)] = True
    return mask


def _ransac_ground(values: NDArray[np.float64]) -> NDArray[np.bool_]:
    """Fallback: one RANSAC plane per tile, fitted to the lowest point of each cell."""
    tile = np.floor(values[:, :2] / _GROUND["ransac_tile_m"]).astype(np.int64)
    _, tile_id = np.unique(tile, axis=0, return_inverse=True)
    mask = np.zeros(len(values), dtype=bool)
    for index in range(tile_id.max() + 1):
        members = np.flatnonzero(tile_id.ravel() == index)
        candidates = values[members[lowest_per_cell(values[members], _GROUND["grid_size_m"])]]
        if len(candidates) < 3:
            continue
        plane, _ = fit_plane_ransac(
            candidates, _GROUND["ransac_distance_m"], _GROUND["ransac_iterations"], seed=index
        )
        predicted = values[members, 0] * plane[0] + values[members, 1] * plane[1] + plane[2]
        mask[members] = np.abs(values[members, 2] - predicted) <= _GROUND["ransac_distance_m"]
    return mask


@contextlib.contextmanager
def _quiet_stdout():
    """Silence output written directly to file descriptor 1 (e.g. by C++ code)."""
    saved = os.dup(1)
    try:
        with open(os.devnull, "w") as devnull:
            os.dup2(devnull.fileno(), 1)
            yield
    finally:
        os.dup2(saved, 1)
        os.close(saved)


def _points(points: ArrayLike) -> NDArray[np.float64]:
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    return values
