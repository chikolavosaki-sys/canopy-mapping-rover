"""Exercise the PNG fallback after a separate viewer process crashes."""

import sys

import pytest

from scripts import show_demo


def test_3d_worker_failure_still_writes_figures(tmp_path, monkeypatch, capsys) -> None:
    pytest.importorskip("kiss_icp")
    worker = tmp_path / "crash.py"
    worker.write_text("import os\nos._exit(12)\n", encoding="utf-8")
    output = tmp_path / "figures"
    monkeypatch.setattr(show_demo, "__file__", str(worker))
    monkeypatch.setattr(sys, "argv", ["show_demo.py", "--view", "3d", "--out", str(output)])

    show_demo.main()

    assert "3D viewer exited with code 12" in capsys.readouterr().out
    assert {image.name for image in output.glob("*.png")} == {
        "forest_map.png", "lidar_scan.png", "odometry.png",
    }
