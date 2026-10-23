"""KISS-ICP on a simulated forest traversal with exact ground-truth poses."""

import json

import numpy as np
import pytest

from canopy.config import section
from canopy.simulation.lidar import simulate_traversal
from canopy.simulation.synthetic_forest import make_forest, traversal_poses


@pytest.fixture(scope="module")
def traversal() -> tuple[list[np.ndarray], list[np.ndarray]]:
    """A short drive through a small forest: exact world poses and sensor-frame scans."""
    forest = make_forest(seed=0, plot_size_m=30.0, n_trees=25)
    sequence = simulate_traversal(forest, traversal_poses(forest, length_m=6.0), sensor_frame=True)
    return [pose for pose, _ in sequence], [scan for _, scan in sequence]


def test_kiss_icp_tracks_synthetic_traversal(traversal, tmp_path) -> None:
    """Estimated positions stay within a loose ATE bound of the exact path."""
    pytest.importorskip("kiss_icp")
    from canopy.lidar_odometry.cli import run_and_save

    poses, frames = traversal
    summary = run_and_save(list(range(len(frames))), frames, tmp_path, reference=poses)

    assert summary["frames"] == len(frames)
    assert summary["ate_rmse_m"] < section("odometry")["test_ate_max_m"]
    assert summary["path_length_m"] > 0
    for name in ("trajectory.tum", "reference.tum", "map.npy", "summary.json"):
        assert (tmp_path / name).exists()
    assert json.loads((tmp_path / "summary.json").read_text())["reference"].startswith("exact")


def test_sensor_frame_scans_sit_around_the_origin(traversal) -> None:
    """Sensor-frame scans are centred on the LiDAR, not on the world position."""
    poses, frames = traversal
    world_position = poses[-1][:2, 3]

    assert np.linalg.norm(world_position) > 5
    assert np.linalg.norm(np.median(frames[-1][:, :2], axis=0)) < np.linalg.norm(world_position)


def test_traversal_poses_face_along_the_path() -> None:
    """Each pose's forward axis points towards the next position."""
    poses = traversal_poses(make_forest(0, 30.0, 2), length_m=2.0)
    step = poses[1][:2, 3] - poses[0][:2, 3]

    assert np.dot(poses[0][:2, 0], step / np.linalg.norm(step)) > 0.9
