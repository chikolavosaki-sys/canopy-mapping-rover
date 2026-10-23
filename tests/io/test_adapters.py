"""Tests for common real-data adapter formats."""

import numpy as np
import pytest

from canopy.io.adapters import load_tree_table, read_tum


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
