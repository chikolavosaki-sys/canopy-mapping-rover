"""Tests for repeated navigation evaluation."""

from canopy.evaluation.nav_eval import evaluate_navigation


def test_navigation_evaluation_writes_one_row_per_seed(tmp_path) -> None:
    """The evaluator produces a CSV with one result for each seed."""
    results = evaluate_navigation(range(2), plot_size_m=10.0, n_trees=2, out_dir=tmp_path)

    assert len(results) == 2
    assert len((tmp_path / "navigation.csv").read_text().splitlines()) == 3
