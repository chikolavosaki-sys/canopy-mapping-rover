"""Tests for the zero-download demo."""

from scripts.run_all import run_demo


def test_run_demo_writes_report_and_summary(tmp_path) -> None:
    """The end-to-end synthetic run writes its user-facing artifacts."""
    summary = run_demo(0, tmp_path)

    assert "navigation_success" in summary
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "ladder_fuel.png").exists()
