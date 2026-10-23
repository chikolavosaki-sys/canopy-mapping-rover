"""Trajectory export helpers."""

from pathlib import Path

import numpy as np


def write_tum(poses: list[tuple[int, np.ndarray]], path: str | Path) -> None:
    """Write timestamped poses in evo-compatible TUM format."""
    with Path(path).open("w", encoding="utf-8") as output:
        for timestamp, pose in poses:
            quaternion = _matrix_to_quaternion(pose[:3, :3])
            values = [timestamp / 1_000_000_000, *pose[:3, 3], *quaternion]
            output.write(" ".join(f"{value:.9g}" for value in values) + "\n")


def _matrix_to_quaternion(matrix: np.ndarray) -> tuple[float, float, float, float]:
    """Convert a rotation matrix to an ``(x, y, z, w)`` quaternion."""
    trace = np.trace(matrix)
    if trace > 0:
        scale = 0.5 / np.sqrt(trace + 1.0)
        return (
            (matrix[2, 1] - matrix[1, 2]) * scale,
            (matrix[0, 2] - matrix[2, 0]) * scale,
            (matrix[1, 0] - matrix[0, 1]) * scale,
            0.25 / scale,
        )
    diagonal = np.diag(matrix)
    index = int(np.argmax(diagonal))
    next_index = (index + 1) % 3
    last_index = (index + 2) % 3
    scale = np.sqrt(1.0 + diagonal[index] - diagonal[next_index] - diagonal[last_index]) * 2
    quaternion = np.zeros(4)
    quaternion[index] = 0.25 * scale
    quaternion[3] = (matrix[last_index, next_index] - matrix[next_index, last_index]) / scale
    quaternion[next_index] = (matrix[next_index, index] + matrix[index, next_index]) / scale
    quaternion[last_index] = (matrix[last_index, index] + matrix[index, last_index]) / scale
    return tuple(quaternion)
