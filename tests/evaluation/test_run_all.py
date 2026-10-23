"""Tests for the zero-download demo."""

import numpy as np
import pytest

from canopy.simulation.synthetic_forest import Forest, ShrubVolume
from scripts.run_all import run_demo, shrub_cells


def test_run_demo_writes_report_and_summary(tmp_path) -> None:
    """The end-to-end run measures odometry and analytics on the scanned map."""
    pytest.importorskip("kiss_icp")
    summary = run_demo(0, tmp_path)

    expected = ("odometry_ate_rmse_m", "map_tree_recall", "cloud_tree_recall", "navigation_success")
    assert all(key in summary for key in expected)
    assert summary["odometry_frames"] > 1
    assert 0 < summary["map_points"]
    for name in ("report.md", "summary.json", "ladder_fuel.png", "trees.json"):
        assert (tmp_path / name).exists()
    assert "Exact-pose map" in (tmp_path / "report.md").read_text()


def test_shrub_cells_cover_the_whole_footprint() -> None:
    """A 2.5 m x 1.5 m shrub marks all overlapped 1 m cells, not only its corner."""
    forest = Forest(
        points=np.zeros((1, 3)),
        labels=np.array(["ground"]),
        trees=[],
        shrubs=[ShrubVolume((1.2, 2.2, 0.5), (3.7, 3.7, 2.0))],
        plot_size_m=10.0,
    )

    cells = shrub_cells(forest, (6, 6), (0.0, 0.0), 1.0)

    assert cells.sum() == 6  # x cells 1-3, y cells 2-3
    assert cells[1:4, 2:4].all()


def test_update_outcomes_replaces_only_the_marked_block(tmp_path) -> None:
    """Text outside the markers survives; the table inside is rewritten."""
    from scripts.run_all import MARKERS, update_outcomes

    doc = tmp_path / "OUTCOMES.md"
    doc.write_text(f"before\n{MARKERS[0]}\nold table\n{MARKERS[1]}\nafter\n")
    keys = (
        "odometry_drift_percent", "odometry_ate_rmse_m", "map_tree_recall", "cloud_tree_recall",
        "map_dbh_rmse_m", "map_ladder_auc", "navigation_success", "exact_tree_recall",
        "exact_dbh_rmse_m", "ground_precision", "ground_recall",
    )
    summary = {key: 0.5 for key in keys} | {"navigation_collisions": 0, "navigation_runs": 80}

    update_outcomes(summary, 3, doc)
    text = doc.read_text()

    assert text.startswith("before\n") and text.endswith(f"{MARKERS[1]}\nafter\n")
    assert "old table" not in text and "Seed 3." in text and "| 0.5000 |" in text
