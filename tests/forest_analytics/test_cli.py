"""Regression checks for the forest analytics command's error reporting."""

import sys

import numpy as np
import pytest

from canopy.forest_analytics import cli, pipeline


@pytest.mark.parametrize("kind", ["missing", "directory"])
def test_missing_config_is_a_usage_error(tmp_path, monkeypatch, capsys, kind) -> None:
    config = tmp_path / "config.yaml"
    if kind == "directory":
        config.mkdir()
    monkeypatch.setattr(
        sys, "argv",
        ["canopy-analyze", "cloud.npy", "--config", str(config), "--out", str(tmp_path)],
    )

    with pytest.raises(SystemExit) as raised:
        cli.main()

    assert raised.value.code == 2
    assert f"--config requires an existing file: {config}" in capsys.readouterr().err


@pytest.mark.parametrize("kind", ["missing", "empty", "invalid shape"])
def test_unusable_cloud_is_a_usage_error(tmp_path, monkeypatch, capsys, kind) -> None:
    cloud = tmp_path / "cloud.npy"
    if kind == "empty":
        np.save(cloud, np.empty((0, 3)))
    elif kind == "invalid shape":
        np.save(cloud, np.zeros((3, 2)))
    monkeypatch.setattr(sys, "argv", ["canopy-analyze", str(cloud), "--out", str(tmp_path)])

    with pytest.raises(SystemExit) as raised:
        cli.main()

    assert raised.value.code == 2
    errors = {
        "missing": "cloud.npy",
        "empty": "point cloud is empty",
        "invalid shape": "points must have shape (N, 3)",
    }
    assert errors[kind] in capsys.readouterr().err


@pytest.mark.parametrize("error_type", [ValueError, OSError])
def test_analysis_and_output_errors_propagate(tmp_path, monkeypatch, error_type) -> None:
    cloud = tmp_path / "cloud.npy"
    np.save(cloud, np.zeros((1, 3)))
    monkeypatch.setattr(sys, "argv", ["canopy-analyze", str(cloud), "--out", str(tmp_path)])

    def fail(points, out_dir):
        raise error_type("analysis or output failure")

    monkeypatch.setattr(pipeline, "analyze_and_write", fail)
    with pytest.raises(error_type, match="analysis or output failure"):
        cli.main()
