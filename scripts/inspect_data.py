"""Inspect downloaded real data without changing it.

Prints bag topics, one decoded LiDAR frame, TreeScope tree-ID mapping, the
HDF5 label layout, and DigiForests folder contents. Writes small summaries
(``topics.md`` per dataset, one sample frame) under the ignored ``data/`` tree.

Run from the repository root: ``python scripts/inspect_data.py``.
"""

import json
import re
from pathlib import Path

import numpy as np

from canopy.io import load_points, save_points
from canopy.io.bag_reader import _pointcloud2_points

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SAMPLES = ROOT / "data" / "samples"
POINTCLOUD_TYPE = "sensor_msgs/msg/PointCloud2"
IMU_TYPE = "sensor_msgs/msg/Imu"
FIELD_TYPES = {1: "int8", 2: "uint8", 3: "int16", 4: "uint16", 5: "int32", 6: "uint32",
               7: "float32", 8: "float64"}


def topic_table(bag: Path) -> tuple[str, list[str], list[str]]:
    """Return a Markdown topic summary plus PointCloud2 and IMU topic names."""
    from rosbags.highlevel import AnyReader

    with AnyReader([bag]) as reader:
        duration_s = reader.duration / 1e9
        version = "ROS2" if reader.is2 else "ROS1"
        lines = [f"# Topics in `{bag.name}`", "",
                 f"- ROS version: {version}", f"- Duration: {duration_s:.1f} s", "",
                 "| Topic | Type | Messages | Rate (Hz) |", "|---|---|---:|---:|"]
        clouds, imus = [], []
        for conn in sorted(reader.connections, key=lambda item: item.topic):
            rate = conn.msgcount / duration_s if duration_s else 0.0
            lines.append(f"| `{conn.topic}` | `{conn.msgtype}` | {conn.msgcount} | {rate:.2f} |")
            if conn.msgtype == POINTCLOUD_TYPE:
                clouds.append(conn.topic)
            if conn.msgtype == IMU_TYPE:
                imus.append(conn.topic)
    lines += ["", f"- PointCloud2 topics: {clouds or 'none'}", f"- IMU topics: {imus or 'none'}"]
    return "\n".join(lines) + "\n", clouds, imus


def first_frame(bag: Path, topic: str) -> tuple[np.ndarray, list[str]]:
    """Decode the first PointCloud2 message on a topic; return XYZ and field names."""
    from rosbags.highlevel import AnyReader

    with AnyReader([bag]) as reader:
        connections = [item for item in reader.connections if item.topic == topic]
        for connection, _, raw in reader.messages(connections=connections):
            message = reader.deserialize(raw, connection.msgtype)
            fields = [f"{field.name}:{FIELD_TYPES.get(field.datatype, field.datatype)}"
                      for field in message.fields]
            return _pointcloud2_points(message), fields
    raise ValueError(f"no messages on {topic}")


def inspect_bags() -> None:
    """Summarise every bag under data/raw and save one frame per dataset."""
    for bag in sorted(RAW.rglob("*.bag")):
        dataset = bag.relative_to(RAW).parts[1]
        table, clouds, imus = topic_table(bag)
        out = RAW / bag.relative_to(RAW).parts[0] / dataset / "topics.md"
        out.write_text(table)
        print(table)
        for topic in clouds[:1]:
            points, fields = first_frame(bag, topic)
            finite = points[np.all(np.isfinite(points), axis=1)]
            print(f"First frame on {topic}: {len(points)} points "
                  f"({len(finite)} finite), fields {fields}")
            SAMPLES.mkdir(parents=True, exist_ok=True)
            save_points(finite, SAMPLES / f"{dataset}_frame0.ply")
            print(f"Saved {SAMPLES / f'{dataset}_frame0.ply'}\n")


def describe_json(value: object, depth: int = 0, max_items: int = 3) -> None:
    """Print the shape of a JSON value without assuming its schema."""
    pad = "  " * depth
    if isinstance(value, dict):
        print(f"{pad}dict with {len(value)} keys: {list(value)[:8]}")
        for key in list(value)[:max_items]:
            print(f"{pad}  [{key!r}] ->")
            describe_json(value[key], depth + 2, max_items)
    elif isinstance(value, list):
        print(f"{pad}list of {len(value)}")
        if value:
            describe_json(value[0], depth + 1, max_items)
    else:
        print(f"{pad}{type(value).__name__}: {value!r}")


def inspect_treescope_trees() -> None:
    """Compare tree PCD filenames with the keys of the VAT-0723 ground-truth JSON."""
    base = RAW / "treescope" / "VAT-0723" / "ground_truth"
    gt_path = base / "measurements" / "VAT-0723M-gt.json"
    if not gt_path.exists():
        print("VAT-0723 ground truth not downloaded; skipping.\n")
        return
    gt = json.loads(gt_path.read_text())
    print("VAT-0723M-gt.json structure:")
    describe_json(gt)
    pcds = sorted((base / "pcds").glob("*.pcd"))
    print(f"\n{len(pcds)} tree PCDs; first names: {[path.stem for path in pcds[:5]]}")
    keys = {str(key) for key in gt} if isinstance(gt, dict) else set()
    for candidate in (lambda p: p.stem, lambda p: re.sub(r"^VAT-0723", "", p.stem)):
        hits = sum(candidate(path) in keys for path in pcds)
        print(f"  filename form e.g. {candidate(pcds[0])!r}: {hits}/{len(pcds)} match JSON keys")
    for path in pcds[:3]:
        points = load_points(path)
        print(f"  {path.name}: {len(points)} points, z {points[:, 2].min():.2f}"
              f"..{points[:, 2].max():.2f} m")
    print()


def inspect_h5() -> None:
    """Print the group/dataset tree of the VAT-0723 HDF5 labels."""
    import h5py

    path = RAW / "treescope" / "VAT-0723" / "ground_truth" / "labels" / "VAT-0723M.h5"
    if not path.exists():
        print("VAT-0723M.h5 not downloaded; skipping.\n")
        return
    print(f"{path.name} layout:")

    def show(name: str, item: object) -> None:
        depth = name.count("/")
        if isinstance(item, h5py.Dataset):
            print(f"{'  ' * depth}{name}: shape {item.shape}, dtype {item.dtype}")
        else:
            print(f"{'  ' * depth}{name}/ attrs {dict(item.attrs)}")

    with h5py.File(path, "r") as handle:
        print(f"  root attrs {dict(handle.attrs)}")
        handle.visititems(show)
    print()


def inspect_wsf_labels() -> None:
    """Show one WSF-19 per-scan DBH label table and its per-tree files."""
    scans = sorted((RAW / "treescope" / "WSF-19" / "ground_truth" / "scans").glob("*"))
    if not scans:
        print("WSF-19 scans not downloaded; skipping.\n")
        return
    scan = scans[0]
    table = np.loadtxt(scan / "single_dbh_labels.txt", ndmin=2)
    print(f"WSF-19: {len(scans)} scan folders; {scan.name} has {len(table)} trees")
    print("  columns x, y, z, dbh, difficulty; first rows:")
    print(np.array2string(table[:3], precision=3))
    print(f"  dbh range {table[:, 3].min():.3f}..{table[:, 3].max():.3f}")
    print(f"  single/: {len(list((scan / 'single').glob('*.pcd')))} tree clouds")
    print(f"  all/: {sorted(path.name for path in (scan / 'all').iterdir())}\n")


def inspect_digiforests() -> None:
    """Print the DigiForests folder tree if it has been downloaded."""
    root = RAW / "digiforests"
    if not root.exists():
        print("DigiForests not downloaded (site was unreachable); skipping.\n")
        return
    for path in sorted(root.rglob("*"))[:50]:
        print(f"  {path.relative_to(root)}")
    print(f"  poses.txt present: {any(root.rglob('poses.txt'))}\n")


def main() -> None:
    """Run every inspection step."""
    inspect_bags()
    inspect_treescope_trees()
    inspect_h5()
    inspect_wsf_labels()
    inspect_digiforests()


if __name__ == "__main__":
    main()
