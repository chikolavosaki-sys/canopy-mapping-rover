"""Stem detection and DBH from height-normalised points.

Approach modelled on the open-source pipelines 3DFIN and FSCT (re-implemented
from their published method, not copied):

1. Take the breast-height slice (1.2-1.4 m) and split it into clusters with
   DBSCAN (Open3D's implementation) on XY.
2. Per cluster, RANSAC a circle: try circles through random point triples and
   keep the one most points agree with, so stray shrub points cannot drag it.
3. Refine on the inliers: an algebraic Kasa fit gives a starting circle, then a
   geometric least-squares fit (distance to the circle) corrects the bias Kasa
   has on partly visible trunks, which a rover usually sees from one side.
4. Reject clusters with few points or inliers, a poor fit, an implausible
   radius, or under ``min_arc_deg`` of visible circle.
5. Verticality: refit in thin slices at 0.8 m and 2.0 m around the same
   centre; a stem must not lean more than ``max_lean_deg`` or change radius by
   more than ``max_radius_change``, and at least one check slice must fit (a
   real trunk continues above and below breast height; shrub patches often
   do not).
"""

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import ArrayLike

from canopy.config import section

_DBH = section("dbh")


@dataclass(frozen=True)
class Stem:
    """A detected stem at breast height."""

    x: float
    y: float
    dbh: float
    fit_residual: float
    n_points: int
    arc_deg: float
    lean_deg: float


@dataclass(frozen=True)
class Circle:
    """Fitted circle with its RMS residual, inlier count, and visible arc."""

    x: float
    y: float
    radius: float
    residual: float
    inliers: int
    arc_deg: float


def detect_stems(points: ArrayLike, seed: int = 0) -> list[Stem]:
    """Find upright stems in height-normalised points and measure their DBH."""
    values = np.asarray(points, dtype=float)
    low, high = _DBH["slice_min_m"], _DBH["slice_max_m"]
    breast = values[(values[:, 2] >= low) & (values[:, 2] < high), :2]
    rng = np.random.default_rng(seed)
    stems = []
    for cluster in _dbscan_clusters(breast):
        circle = fit_circle(cluster, rng)
        if circle is None or not _plausible(circle, len(cluster)):
            continue
        lean = _lean_deg(values, circle, rng)
        if lean is None or lean > _DBH["max_lean_deg"]:
            continue
        stems.append(Stem(circle.x, circle.y, 2 * circle.radius, circle.residual,
                          len(cluster), circle.arc_deg, lean))
    return stems


def fit_circle(xy: np.ndarray, rng: np.random.Generator) -> Circle | None:
    """RANSAC + Kasa + geometric refinement; None if no circle has enough support."""
    if len(xy) < 3:
        return None
    best = _ransac_inliers(xy, rng)
    if best.sum() < 3:
        return None
    centre, radius = _refine(xy[best], *_kasa(xy[best]))
    distance = np.linalg.norm(xy - centre, axis=1)
    inliers = np.abs(distance - radius) <= _DBH["ransac_inlier_m"]
    if inliers.sum() < 3:
        return None
    residual = float(np.sqrt(np.mean((distance[inliers] - radius) ** 2)))
    arc = _arc_deg(xy[inliers] - centre)
    return Circle(float(centre[0]), float(centre[1]), radius, residual, int(inliers.sum()), arc)


def remove_stem_points(
    points: ArrayLike, stems: list[Stem], margin: float = _DBH["stem_removal_margin_m"]
) -> np.ndarray:
    """Drop points within (DBH / 2 + margin) of any detected stem axis, at all heights."""
    values = np.asarray(points, dtype=float)
    keep = np.ones(len(values), dtype=bool)
    for stem in stems:
        near = np.hypot(values[:, 0] - stem.x, values[:, 1] - stem.y) <= stem.dbh / 2 + margin
        keep &= ~near
    return values[keep]


def stems_to_rows(stems: list[Stem]) -> list[dict[str, float | int]]:
    """Convert stems to CSV/JSON-ready rows."""
    return [asdict(stem) for stem in stems]


def _dbscan_clusters(xy: np.ndarray) -> list[np.ndarray]:
    """DBSCAN on the slice's XY coordinates (Open3D ``cluster_dbscan``); noise is dropped."""
    import open3d as o3d

    if len(xy) < _DBH["dbscan_min_points"]:
        return []
    cloud = o3d.geometry.PointCloud(
        o3d.utility.Vector3dVector(np.column_stack((xy, np.zeros(len(xy)))))
    )
    labels = np.asarray(cloud.cluster_dbscan(_DBH["dbscan_eps_m"], _DBH["dbscan_min_points"]))
    return [xy[labels == label] for label in range(labels.max() + 1)]


def _plausible(circle: Circle, cluster_size: int) -> bool:
    return (
        cluster_size >= _DBH["min_points"]
        and circle.inliers >= _DBH["min_inlier_fraction"] * cluster_size
        and _DBH["min_radius_m"] <= circle.radius <= _DBH["max_radius_m"]
        and circle.residual <= _DBH["max_fit_residual_m"]
        and circle.arc_deg >= _DBH["min_arc_deg"]
    )


def _ransac_inliers(xy: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Inlier mask of the circle through 3 random points that most points agree with."""
    best = np.zeros(len(xy), dtype=bool)
    for _ in range(_DBH["ransac_iterations"]):
        circle = _circle_through(xy[rng.choice(len(xy), 3, replace=False)])
        if circle is None or circle[1] > _DBH["max_radius_m"]:
            continue
        centre, radius = circle
        inliers = np.abs(np.linalg.norm(xy - centre, axis=1) - radius) <= _DBH["ransac_inlier_m"]
        if inliers.sum() > best.sum():
            best = inliers
    return best


def _circle_through(three: np.ndarray) -> tuple[np.ndarray, float] | None:
    """Circumcircle of three points, or None if they are (nearly) in a line."""
    (ax, ay), (bx, by), (cx, cy) = three
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None
    a2, b2, c2 = ax * ax + ay * ay, bx * bx + by * by, cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    centre = np.array([ux, uy])
    return centre, float(np.linalg.norm(three[0] - centre))


def _kasa(xy: np.ndarray) -> tuple[np.ndarray, float]:
    """Algebraic (Kasa) circle fit: linear least squares on x^2 + y^2 = 2ax + 2by + c."""
    design = np.column_stack((2 * xy, np.ones(len(xy))))
    a, b, c = np.linalg.lstsq(design, np.sum(xy**2, axis=1), rcond=None)[0]
    return np.array([a, b]), float(np.sqrt(max(c + a * a + b * b, 0.0)))


def _refine(xy: np.ndarray, centre: np.ndarray, radius: float) -> tuple[np.ndarray, float]:
    """Geometric fit: minimise each point's distance to the circle, starting from Kasa."""
    from scipy.optimize import least_squares

    fit = least_squares(
        lambda p: np.hypot(xy[:, 0] - p[0], xy[:, 1] - p[1]) - p[2], [*centre, radius]
    )
    return fit.x[:2], float(abs(fit.x[2]))


def _arc_deg(offsets: np.ndarray) -> float:
    """Angular extent of points around the centre: 360 minus the largest empty gap."""
    angles = np.sort(np.arctan2(offsets[:, 1], offsets[:, 0]))
    gaps = np.diff(np.concatenate((angles, angles[:1] + 2 * np.pi)))
    return float(np.degrees(2 * np.pi - gaps.max()))


def _lean_deg(values: np.ndarray, circle: Circle, rng: np.random.Generator) -> float | None:
    """Largest lean (deg) between breast height and the check slices; None if unchecked.

    Returns ``inf`` when a check slice fits a circle whose radius is too
    different from the breast-height one (not a single upright stem).
    """
    half, search = _DBH["verticality_half_height_m"], circle.radius + 0.15
    near = np.hypot(values[:, 0] - circle.x, values[:, 1] - circle.y) <= search
    breast_height = (_DBH["slice_min_m"] + _DBH["slice_max_m"]) / 2
    leans = []
    for height in _DBH["verticality_slices_m"]:
        band = values[near & (np.abs(values[:, 2] - height) <= half), :2]
        check = fit_circle(band, rng) if len(band) >= _DBH["dbscan_min_points"] else None
        if check is None:
            continue
        if abs(check.radius - circle.radius) > _DBH["max_radius_change"] * circle.radius:
            return float("inf")
        offset = np.hypot(check.x - circle.x, check.y - circle.y)
        leans.append(np.degrees(np.arctan2(offset, abs(breast_height - height))))
    return max(leans) if leans else None
