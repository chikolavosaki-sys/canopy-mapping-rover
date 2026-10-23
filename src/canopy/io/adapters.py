"""Common formats for real-dataset adapters."""

import csv
import json
from pathlib import Path

import numpy as np


def read_tum(path: str | Path) -> list[tuple[float, np.ndarray]]:
    """Read an evo/TUM trajectory as seconds and homogeneous poses."""
    poses = []
    for line_number, line in enumerate(Path(path).read_text().splitlines(), 1):
        fields = line.split()
        if not fields or fields[0].startswith("#"):
            continue
        if len(fields) != 8:
            raise ValueError(f"TUM line {line_number} must contain 8 fields")
        timestamp, x, y, z, qx, qy, qz, qw = map(float, fields)
        pose = np.eye(4, dtype=np.float64)
        pose[:3, :3] = _quaternion_matrix(qx, qy, qz, qw)
        pose[:3, 3] = (x, y, z)
        poses.append((timestamp, pose))
    return poses


def load_tree_table(path: str | Path) -> list[dict[str, float]]:
    """Load a tree table with x, y, and DBH fields from CSV or JSON.

    Dataset-specific field names must be mapped by an adapter before calling
    this function. This avoids silently guessing what an unknown source column
    means.
    """
    source = Path(path)
    if source.suffix.lower() == ".json":
        records = json.loads(source.read_text())
    elif source.suffix.lower() == ".csv":
        with source.open(newline="", encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
    else:
        raise ValueError("tree tables must be CSV or JSON")
    if not isinstance(records, list):
        raise ValueError("tree table must contain a list of records")
    required = {"x", "y", "dbh"}
    output = []
    for index, record in enumerate(records):
        missing = required - record.keys()
        if missing:
            raise ValueError(f"tree record {index} is missing fields: {sorted(missing)}")
        output.append({key: float(record[key]) for key in required})
    return output


def _quaternion_matrix(x: float, y: float, z: float, w: float) -> np.ndarray:
    norm = x * x + y * y + z * z + w * w
    if norm == 0:
        raise ValueError("trajectory quaternion cannot be zero")
    scale = 2.0 / norm
    return np.array(
        [
            [1 - scale * (y * y + z * z), scale * (x * y - z * w), scale * (x * z + y * w)],
            [scale * (x * y + z * w), 1 - scale * (x * x + z * z), scale * (y * z - x * w)],
            [scale * (x * z - y * w), scale * (y * z + x * w), 1 - scale * (x * x + y * y)],
        ]
    )
