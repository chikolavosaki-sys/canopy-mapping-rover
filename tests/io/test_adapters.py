"""Tests for common real-data adapter formats."""

import numpy as np
import pytest

from canopy.io.adapters import load_tree_table, read_tum
from canopy.io.bag_reader import iter_odometry, iter_pointclouds


def test_read_tum_and_tree_table(tmp_path) -> None:
    """TUM and CSV adapters return common project structures."""
    tum = tmp_path / "poses.tum"
    tum.write_text("1 2 3 4 0 0 0 1\n")
    table = tmp_path / "trees.csv"
    table.write_text("x,y,dbh\n1,2,0.3\n")

    timestamp, pose = read_tum(tum)[0]

    assert timestamp == 1
    np.testing.assert_allclose(pose[:3, 3], [2, 3, 4])
    assert load_tree_table(table) == [{"x": 1.0, "y": 2.0, "dbh": 0.3}]


def test_tree_table_requires_explicit_common_fields(tmp_path) -> None:
    """Unknown dataset-specific column names fail instead of being guessed."""
    table = tmp_path / "trees.csv"
    table.write_text("east,north,diameter\n1,2,0.3\n")

    with pytest.raises(ValueError, match="missing fields"):
        load_tree_table(table)


def test_ros_bag_uses_requested_topic_and_decodes_padded_big_endian_rows(tmp_path) -> None:
    """Check topic filtering, row strides, byte order and invalid LiDAR returns."""
    pytest.importorskip("rosbags")
    from rosbags.rosbag1 import Writer
    from rosbags.typesys import Stores, get_typestore

    store = get_typestore(Stores.ROS1_NOETIC)
    header = store.types["std_msgs/msg/Header"](
        0, store.types["builtin_interfaces/msg/Time"](0, 0), "lidar"
    )
    point_field = store.types["sensor_msgs/msg/PointField"]
    fields = [point_field(name, offset * 4, 7, 1) for offset, name in enumerate("xyz")]
    rows = np.array([[[1, 2, 3], [np.nan, 1, 2]], [[4, 5, 6], [7, 8, 9]]], dtype=">f4")
    data = np.frombuffer(b"".join(row.tobytes() + b"\x00" * 4 for row in rows), dtype=np.uint8)
    msgtype = "sensor_msgs/msg/PointCloud2"
    message = store.types[msgtype](header, 2, 2, fields, True, 12, 28, data, False)
    bag = tmp_path / "recording.bag"
    with Writer(bag) as writer:
        connection = writer.add_connection("/lidar", msgtype, typestore=store)
        writer.write(connection, 123, store.serialize_ros1(message, msgtype))

    assert list(iter_pointclouds(bag, "/missing")) == []
    assert list(iter_odometry(bag, "/lidar")) == []
    (stamp, points), = iter_pointclouds(bag, "/lidar")
    assert stamp == 123
    np.testing.assert_array_equal(points, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
