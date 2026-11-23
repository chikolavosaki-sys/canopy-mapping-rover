"""Per-point features that describe the local shape around each LiDAR point.

A single point is just (x, y, z); on its own it says nothing about what it
hit. So for every point we look at its nearest neighbours and describe the
*shape* they form, using the eigenvalues l1 >= l2 >= l3 of their covariance
(how spread out they are along their three main directions):

- linearity  (l1 - l2) / l1: points lie on a line (trunk edges, branches)
- planarity  (l2 - l3) / l1: points lie on a flat sheet (ground, rock faces)
- scattering l3 / l1:        points are spread in all directions (leaves)
- verticality: how upright the surface is (ground ~0, trunk surface ~1)
- vertical_direction: how vertical the main direction is (a trunk ~1)

plus the point's height above ground, the height spread of its neighbours and
the neighbourhood size (dense or sparse). These are standard features in LiDAR
point classification; the model learns which combinations mean which class.
"""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from canopy.config import section

FEATURE_NAMES = (
    "height_m",
    "linearity",
    "planarity",
    "scattering",
    "verticality",
    "vertical_direction",
    "height_spread_m",
    "neighbourhood_radius_m",
)


def point_features(
    cloud: ArrayLike,
    query: ArrayLike | None = None,
    neighbours: int = section("ml")["neighbours"],
) -> NDArray[np.float64]:
    """Return an (M, 8) feature table for ``query`` points, using neighbours from ``cloud``.

    Both must be height-normalised (z = height above ground). ``query``
    defaults to every point of ``cloud``; passing a subset is much faster.
    """
    from scipy.spatial import cKDTree

    points = _points(cloud)
    targets = points if query is None else _points(query)
    k = min(neighbours, len(points))
    if k < 3:
        raise ValueError("need at least 3 points to describe local shape")
    distances, index = cKDTree(points).query(targets, k=k)
    groups = points[index]  # (M, k, 3)
    centred = groups - groups.mean(axis=1, keepdims=True)
    covariance = np.einsum("mki,mkj->mij", centred, centred) / k
    values, vectors = np.linalg.eigh(covariance)  # ascending: l3, l2, l1
    l3, l2, l1 = (np.maximum(values[:, i], 0.0) for i in range(3))
    safe = np.where(l1 > 0, l1, 1.0)
    normal_z = np.abs(vectors[:, 2, 0])  # z of the smallest-spread direction
    main_z = np.abs(vectors[:, 2, 2])  # z of the largest-spread direction
    return np.column_stack(
        (
            targets[:, 2],
            (l1 - l2) / safe,
            (l2 - l3) / safe,
            l3 / safe,
            1.0 - normal_z,
            main_z,
            groups[:, :, 2].std(axis=1),
            distances[:, -1],
        )
    )


def _points(values: ArrayLike) -> NDArray[np.float64]:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    return array
