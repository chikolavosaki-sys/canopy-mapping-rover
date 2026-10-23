"""Simple unicycle rover simulation against synthetic forest geometry."""

from dataclasses import dataclass

import numpy as np

from canopy.config import section
from canopy.navigation.controller import Controller, MotionState
from canopy.navigation.sectors import nearest_obstacles

from .synthetic_forest import Forest, Sensor, simulate_scan

_NAV = section("navigation")


@dataclass(frozen=True)
class Rover:
    """Rover state and physical limits."""

    pose: np.ndarray
    radius: float = _NAV["rover_radius_m"]
    step_size: float = _NAV["step_size_m"]


@dataclass(frozen=True)
class RunResult:
    """Navigation run measurements."""

    poses: list[np.ndarray]
    reached_goal: bool
    collision: bool
    timed_out: bool
    path_length: float


def run_rover(
    forest: Forest,
    start: np.ndarray,
    goal: np.ndarray,
    controller: Controller,
    sensor: Sensor = Sensor(),
    max_steps: int = _NAV["max_steps"],
    rover_radius: float = _NAV["rover_radius_m"],
    step_size: float = _NAV["step_size_m"],
    turn_angle_deg: float = _NAV["turn_angle_deg"],
) -> RunResult:
    """Drive a rover toward a goal and report collisions and timeout."""
    pose = np.asarray(start, dtype=float).copy()
    goal = np.asarray(goal, dtype=float)
    poses = [pose.copy()]
    turn = np.deg2rad(turn_angle_deg)
    path_length = 0.0
    collision = False
    for _ in range(max_steps):
        delta = goal[:2] - pose[:2, 3]
        if np.linalg.norm(delta) <= rover_radius:
            return RunResult(poses, True, collision, False, path_length)
        scan = simulate_scan(forest, pose, sensor)
        local = _world_to_local(scan, pose)
        state = controller.update(nearest_obstacles(local), _heading_error(pose, goal))
        heading = np.arctan2(delta[1], delta[0])
        if state == MotionState.TURN_LEFT:
            heading += turn
        elif state == MotionState.TURN_RIGHT:
            heading -= turn
        elif state == MotionState.STOP:
            poses.append(pose.copy())
            continue
        step = min(step_size, np.linalg.norm(delta))
        next_position = pose[:2, 3] + step * np.array([np.cos(heading), np.sin(heading)])
        if _collides(next_position, forest, rover_radius):
            collision = True
            break
        pose = _pose_at(next_position, heading)
        path_length += step
        poses.append(pose.copy())
    return RunResult(poses, False, collision, not collision, path_length)


def _world_to_local(points: np.ndarray, pose: np.ndarray) -> np.ndarray:
    inverse = np.linalg.inv(pose)
    return (inverse @ np.column_stack((points, np.ones(len(points)))).T).T[:, :3]


def _pose_at(position: np.ndarray, heading: float) -> np.ndarray:
    pose = np.eye(4)
    pose[:2, :2] = [[np.cos(heading), -np.sin(heading)], [np.sin(heading), np.cos(heading)]]
    pose[:2, 3] = position
    return pose


def _heading_error(pose: np.ndarray, goal: np.ndarray) -> float:
    desired = np.arctan2(goal[1] - pose[1, 3], goal[0] - pose[0, 3])
    current = np.arctan2(pose[1, 0], pose[0, 0])
    return np.arctan2(np.sin(desired - current), np.cos(desired - current))


def _collides(position: np.ndarray, forest: Forest, radius: float) -> bool:
    obstacles = forest.points[forest.labels == "stem"]
    return bool(np.any(np.linalg.norm(obstacles[:, :2] - position, axis=1) <= radius))
