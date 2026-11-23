"""Labelled training data from simulated forests.

Because we generate the forest ourselves, the simulated LiDAR knows what every
ray hit, so every point comes with its true class for free. One forest gives:
a drive through it (exact poses, so odometry drift does not mix in), the scans
merged into one cloud, heights measured above the ground found by our ground
step, and a balanced sample of points per class with their features.
"""

import numpy as np
from numpy.typing import NDArray

from canopy.config import section
from canopy.forest_analytics.ground import normalize_heights
from canopy.simulation.lidar import scan_with_labels
from canopy.simulation.synthetic_forest import make_forest, traversal_poses

from .features import point_features

_ML = section("ml")


def labelled_forest_cloud(seed: int) -> tuple[NDArray[np.float64], NDArray[np.str_]]:
    """Height-normalised points and true labels from one simulated drive."""
    cfg = _ML["forest"]
    forest = make_forest(seed, cfg["plot_size_m"], cfg["tree_count"], cfg["points_per_tree"])
    scans = [
        scan_with_labels(forest, pose, seed=index)
        for index, pose in enumerate(traversal_poses(forest))
    ]
    points = np.vstack([scan[0] for scan in scans])
    labels = np.concatenate([scan[1] for scan in scans])
    _, normalized, _ = normalize_heights(points)
    return normalized, labels


def balanced_sample(
    labels: NDArray[np.str_], per_class: int, rng: np.random.Generator
) -> NDArray[np.int64]:
    """Indices with at most ``per_class`` points of each class (all, if fewer exist)."""
    chosen = []
    for name in _ML["classes"]:
        members = np.flatnonzero(labels == name)
        if len(members) > per_class:
            members = rng.choice(members, per_class, replace=False)
        chosen.append(members)
    return np.sort(np.concatenate(chosen))


def build_dataset(
    seeds: list[int], per_class: int = _ML["samples_per_class"]
) -> tuple[NDArray[np.float64], NDArray[np.str_]]:
    """Feature table X and labels y from several simulated forests."""
    features, targets = [], []
    for seed in seeds:
        cloud, labels = labelled_forest_cloud(seed)
        picked = balanced_sample(labels, per_class, np.random.default_rng(seed))
        features.append(point_features(cloud, cloud[picked]))
        targets.append(labels[picked])
    return np.vstack(features), np.concatenate(targets)
