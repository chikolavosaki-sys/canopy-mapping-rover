"""Repeated synthetic navigation evaluation."""

import csv
from pathlib import Path

from canopy.navigation.controller import Controller
from canopy.simulation.rover_sim import RunResult, run_rover
from canopy.simulation.synthetic_forest import make_forest


def evaluate_navigation(
    seeds: range,
    plot_size_m: float = 30.0,
    n_trees: int = 10,
    out_dir: str | Path | None = None,
) -> list[RunResult]:
    """Run one start-to-goal traversal per seed and optionally write CSV."""
    results = []
    for seed in seeds:
        forest = make_forest(seed, plot_size_m, n_trees)
        start = _pose(1.0, plot_size_m / 2)
        goal = [plot_size_m - 1.0, plot_size_m / 2, 0.0]
        result = run_rover(forest, start, goal, Controller())
        results.append(result)
    if out_dir is not None:
        _write_results(results, Path(out_dir))
    return results


def _pose(x: float, y: float) -> list[list[float]]:
    return [[1.0, 0.0, 0.0, x], [0.0, 1.0, 0.0, y], [0.0, 0.0, 1.0, 0.0], [0, 0, 0, 1]]


def _write_results(results: list[RunResult], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "navigation.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["run", "success", "collision", "timeout", "path_length"])
        for index, result in enumerate(results):
            writer.writerow(
                [index, result.reached_goal, result.collision, result.timed_out, result.path_length]
            )
