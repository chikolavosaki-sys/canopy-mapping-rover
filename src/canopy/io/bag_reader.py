"""Optional ROS1/ROS2 bag readers that do not require ROS installation."""

from pathlib import Path
from typing import Iterator

import numpy as np


def list_topics(path: str | Path) -> list[str]:
    """List topic names in a ROS1 or ROS2 bag using ``rosbags``."""
    from rosbags.highlevel import AnyReader

    with AnyReader([Path(path)]) as reader:
        return sorted(connection.topic for connection in reader.connections)


def iter_pointclouds(path: str | Path, topic: str) -> Iterator[tuple[int, np.ndarray]]:
    """Yield ``(timestamp, (N, 3) points)`` for one PointCloud2 topic."""
    from rosbags.highlevel import AnyReader
    from sensor_msgs_py import point_cloud2

    with AnyReader([Path(path)]) as reader:
        connections = [item for item in reader.connections if item.topic == topic]
        for connection, timestamp, raw in reader.messages(connections=connections):
            message = reader.deserialize(raw, connection.msgtype)
            fields = list(point_cloud2.read_points(message, field_names=("x", "y", "z")))
            yield timestamp, np.asarray(fields, dtype=np.float64)


def iter_odometry(path: str | Path, topic: str) -> Iterator[tuple[int, np.ndarray]]:
    """Yield ``(timestamp, 4x4 pose)`` from a nav_msgs/Odometry topic."""
    from rosbags.highlevel import AnyReader

    with AnyReader([Path(path)]) as reader:
        connections = [item for item in reader.connections if item.topic == topic]
        for connection, timestamp, raw in reader.messages(connections=connections):
            message = reader.deserialize(raw, connection.msgtype)
            yield timestamp, _odometry_pose(message)


def _odometry_pose(message: object) -> np.ndarray:
    """Convert a ROS odometry message into a homogeneous pose matrix."""
    pose = message.pose.pose
    q = pose.orientation
    rotation = _quaternion_matrix(q.x, q.y, q.z, q.w)
    result = np.eye(4, dtype=np.float64)
    result[:3, :3] = rotation
    result[:3, 3] = (pose.position.x, pose.position.y, pose.position.z)
    return result


def _quaternion_matrix(x: float, y: float, z: float, w: float) -> np.ndarray:
    """Return a rotation matrix from a quaternion."""
    norm = x * x + y * y + z * z + w * w
    if norm == 0:
        raise ValueError("odometry quaternion cannot be zero")
    scale = 2.0 / norm
    return np.array(
        [
            [1 - scale * (y * y + z * z), scale * (x * y - z * w), scale * (x * z + y * w)],
            [scale * (x * y + z * w), 1 - scale * (x * x + z * z), scale * (y * z - x * w)],
            [scale * (x * z - y * w), scale * (y * z + x * w), 1 - scale * (x * x + y * y)],
        ]
    )
