"""Repeated simulator navigation runs over several seeds and forest densities."""

import csv
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from canopy.config import section
from canopy.navigation.controller import Controller
from canopy.simulation.rover_sim import RunResult, collides, run_rover
from canopy.simulation.synthetic_forest import Forest, make_forest

_NAV = section("navigation")
_EVAL = _NAV["eval"]


@dataclass(frozen=True)
class NavRun:
    """One navigation run and the scenario it came from."""

    tree_count: int
    seed: int
    result: RunResult


def evaluate_navigation(
    seeds: Iterable[int],
    tree_counts: Sequence[int] = tuple(_EVAL["tree_counts"]),
    plot_size_m: float = _EVAL["plot_size_m"],
    out_dir: str | Path | None = None,
) -> list[NavRun]:
    """Drive across a fresh forest for every (density, seed) pair; optionally write CSVs."""
    runs = []
    for tree_count in tree_counts:
        for seed in seeds:
            forest = make_forest(seed, plot_size_m, tree_count)
            start, goal = start_and_goal(forest)
            runs.append(NavRun(tree_count, seed, run_rover(forest, start, goal, Controller())))
    if out_dir is not None:
        _write_runs(runs, Path(out_dir))
        _write_summary(summarise(runs), Path(out_dir))
    return runs


def start_and_goal(forest: Forest) -> tuple[np.ndarray, np.ndarray]:
    """Start at the left edge, goal at the right, shifted sideways until both are clear.

    Without this, a tree generated on top of the start would count as a
    navigation failure that no controller could avoid.
    """
    size, margin = forest.plot_size_m, _EVAL["start_goal_margin_m"]
    clearance = _NAV["rover_radius_m"] + _EVAL["start_clearance_m"]
    for offset in _sideways_offsets(size / 2 - margin, _EVAL["start_search_step_m"]):
        y = size / 2 + offset
        start, goal = np.array([margin, y]), np.array([size - margin, y])
        if not (collides(start, forest, clearance) or collides(goal, forest, clearance)):
            pose = np.eye(4)
            pose[:2, 3] = start
            return pose, goal
    raise ValueError("no clear start/goal line found in this forest")


def summarise(runs: list[NavRun]) -> list[dict[str, float | int | str]]:
    """Success, collisions, time-outs and path ratio per density, plus an overall row."""
    groups: dict[str, list[NavRun]] = {}
    for run in runs:
        groups.setdefault(str(run.tree_count), []).append(run)
    groups["all"] = runs
    rows = []
    for name, group in groups.items():
        results = [run.result for run in group]
        ratios = [result.path_ratio for result in results if result.reached_goal]
        rows.append({
            "tree_count": name,
            "runs": len(results),
            "success_rate": sum(result.reached_goal for result in results) / len(results),
            "collisions": sum(result.collision for result in results),
            "timeouts": sum(result.timed_out for result in results),
            "mean_path_ratio": float(np.mean(ratios)) if ratios else float("nan"),
        })
    return rows


def _sideways_offsets(limit: float, step: float) -> list[float]:
    """0, +step, -step, +2 step, ... up to ``limit``: try the plot centre line first."""
    offsets = [0.0]
    for k in range(1, int(limit / step) + 1):
        offsets += [k * step, -k * step]
    return offsets


def _write_runs(runs: list[NavRun], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "navigation.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["tree_count", "seed", "success", "collision", "timeout",
                         "path_length_m", "path_ratio", "steps"])
        for run in runs:
            result = run.result
            writer.writerow([run.tree_count, run.seed, result.reached_goal, result.collision,
                             result.timed_out, f"{result.path_length:.2f}",
                             f"{result.path_ratio:.3f}", len(result.poses) - 1])


def _write_summary(rows: list[dict[str, float | int | str]], out_dir: Path) -> None:
    with (out_dir / "navigation_summary.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
