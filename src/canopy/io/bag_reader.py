"""Optional ROS1/ROS2 bag readers that do not require ROS installation."""

from collections.abc import Iterator
from pathlib import Path

import numpy as np


def list_topics(path: str | Path) -> list[str]:
    """List topic names in a ROS1 or ROS2 bag using ``rosbags``."""
    from rosbags.highlevel import AnyReader

    with AnyReader([Path(path)]) as reader:
        return sorted(connection.topic for connection in reader.connections)


def iter_pointclouds(path: str | Path, topic: str) -> Iterator[tuple[int, np.ndarray]]:
    """Yield ``(timestamp, (N, 3) points)`` for one PointCloud2 topic."""
    from rosbags.highlevel import AnyReader

    with AnyReader([Path(path)]) as reader:
        connections = [item for item in reader.connections if item.topic == topic]
        for connection, timestamp, raw in reader.messages(connections=connections):
            message = reader.deserialize(raw, connection.msgtype)
            yield timestamp, _pointcloud2_points(message)


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


def _pointcloud2_points(message: object) -> np.ndarray:
    """Decode XYZ fields without requiring a ROS installation."""
    fields = {field.name: field for field in message.fields}
    if not {"x", "y", "z"} <= fields.keys():
        raise ValueError("PointCloud2 message must contain x, y, and z fields")
    datatype = {7: "f4", 8: "f8"}
    descriptors = []
    for name in ("x", "y", "z"):
        field = fields[name]
        if field.datatype not in datatype or field.count != 1:
            raise ValueError("XYZ fields must be scalar float32 or float64 values")
        descriptors.append((name, field.offset, datatype[field.datatype]))
    dtype = np.dtype(
        {
            "names": [item[0] for item in descriptors],
            "formats": [item[2] for item in descriptors],
            "offsets": [item[1] for item in descriptors],
            "itemsize": message.point_step,
        }
    )
    points = np.frombuffer(bytes(message.data), dtype=dtype, count=message.width * message.height)
    return np.column_stack((points["x"], points["y"], points["z"])).astype(np.float64)


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
