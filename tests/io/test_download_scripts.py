"""Tests that dataset scripts are instruction-only."""

from datasets.download_scripts.digiforests import validate


def test_dataset_validator_only_reports_missing_layout(tmp_path) -> None:
    """Validation does not create files or fetch data."""
    assert validate(tmp_path) == ["pointclouds", "labels"]
    assert list(tmp_path.iterdir()) == []
