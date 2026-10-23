"""Tests for repeated navigation evaluation."""

import csv

import numpy as np

from canopy.evaluation.nav_eval import evaluate_navigation, start_and_goal, summarise
from canopy.simulation.rover_sim import collides
from canopy.simulation.synthetic_forest import make_forest


def test_navigation_runs_every_seed_and_density_and_writes_csvs(tmp_path) -> None:
    """2 seeds x 2 densities give 4 runs, a per-run CSV, and a summary with an overall row."""
    runs = evaluate_navigation(range(2), tree_counts=(5, 10), plot_size_m=20.0, out_dir=tmp_path)

    assert [(run.tree_count, run.seed) for run in runs] == [(5, 0), (5, 1), (10, 0), (10, 1)]
    with (tmp_path / "navigation.csv").open() as handle:
        assert len(list(csv.DictReader(handle))) == 4
    with (tmp_path / "navigation_summary.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert [row["tree_count"] for row in rows] == ["5", "10", "all"]
    assert rows[-1]["runs"] == "4"


def test_start_and_goal_are_never_inside_an_obstacle() -> None:
    """Even in a dense forest, the chosen start and goal have clearance."""
    forest = make_forest(3, 30.0, 80)
    start, goal = start_and_goal(forest)

    assert not collides(start[:2, 3], forest, 1.0)
    assert not collides(goal, forest, 1.0)
    assert start[1, 3] == goal[1]


def test_summary_counts_outcomes() -> None:
    """Success rate and path ratio come from the run results."""
    runs = evaluate_navigation(range(3), tree_counts=(5,), plot_size_m=20.0)
    overall = summarise(runs)[-1]

    assert overall["runs"] == 3
    assert overall["success_rate"] + (overall["collisions"] + overall["timeouts"]) / 3 == 1
    assert np.isnan(overall["mean_path_ratio"]) or overall["mean_path_ratio"] >= 1.0
