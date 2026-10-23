"""Unicycle rover driving through a synthetic forest, steered by the controller.

Each step: scan with the simulated LiDAR, summarise obstacles in the rover
frame, ask the controller for a state, then move. FORWARD drives one step
(steering towards the goal when clear), TURN_LEFT/RIGHT rotate in place, and
STOP waits. A collision is the rover's footprint circle touching a trunk
cylinder or a rock's cross-section at the rover's ground clearance (lower
parts pass under the chassis, which is also why the LiDAR ignores them).
Shrubs are soft and do not count, though the rover still avoids them.
"""

from dataclasses import dataclass

import numpy as np

from canopy.config import section
from canopy.navigation.controller import Controller, MotionState
from canopy.navigation.sectors import corridor_clearance, footprint_clearance, nearest_obstacles

from .synthetic_forest import Forest, Sensor, simulate_scan

_NAV = section("navigation")


@dataclass(frozen=True)
class RunResult:
    """Navigation run measurements."""

    poses: list[np.ndarray]
    reached_goal: bool
    collision: bool
    timed_out: bool
    path_length: float
    straight_line: float

    @property
    def path_ratio(self) -> float:
        """Driven distance divided by the straight start-goal distance (1.0 is ideal)."""
        return self.path_length / self.straight_line if self.straight_line else float("nan")


def run_rover(
    forest: Forest,
    start: np.ndarray,
    goal: np.ndarray,
    controller: Controller,
    sensor: Sensor = Sensor(),
    max_steps: int = _NAV["max_steps"],
    rover_radius: float = _NAV["rover_radius_m"],
    step_size: float = _NAV["step_size_m"],
) -> RunResult:
    """Drive from ``start`` (4x4 pose on the ground) towards ``goal`` (x, y, ...)."""
    pose = np.asarray(start, dtype=float).copy()
    target = np.asarray(goal, dtype=float)[:2]
    turn = np.deg2rad(_NAV["turn_angle_deg"])
    poses, path_length = [pose.copy()], 0.0
    straight = float(np.linalg.norm(target - pose[:2, 3]))
    for _ in range(max_steps):
        if np.linalg.norm(target - pose[:2, 3]) <= _NAV["goal_tolerance_m"]:
            return RunResult(poses, True, False, False, path_length, straight)
        local = _sense(forest, pose, sensor)
        sectors, goal_heading = nearest_obstacles(local), _goal_heading(pose, target)
        state = controller.update(sectors, corridor_clearance(local), goal_heading)
        heading = _heading(pose)
        if state == MotionState.TURN_LEFT:
            pose = _pose_at(pose[:2, 3], heading + turn)
        elif state == MotionState.TURN_RIGHT:
            pose = _pose_at(pose[:2, 3], heading - turn)
        elif state == MotionState.FORWARD:
            remaining = float(np.linalg.norm(target - pose[:2, 3]))
            steer = _safe_steer(local, sectors, goal_heading, controller, min(step_size, remaining))
            if steer is None:  # no safe step: rotate away from the closest obstacle instead
                poses.append(_pose_at(pose[:2, 3], heading + _away(local) * turn))
                pose = poses[-1].copy()
                continue
            heading += steer
            position = pose[:2, 3] + min(step_size, remaining) * np.array(
                [np.cos(heading), np.sin(heading)]
            )
            if collides(position, forest, rover_radius):
                return RunResult(poses, False, True, False, path_length, straight)
            path_length += min(step_size, remaining)
            pose = _pose_at(position, heading)
        poses.append(pose.copy())
    return RunResult(poses, False, False, True, path_length, straight)


def collides(position: np.ndarray, forest: Forest, rover_radius: float) -> bool:
    """True if a rover circle at ``position`` overlaps any trunk or rock."""
    clearance = _NAV["obstacle_min_height_m"]
    discs = [(tree.x, tree.y, tree.dbh / 2) for tree in forest.trees]
    discs += [
        (rock.x, rock.y, np.sqrt(rock.radius**2 - clearance**2))
        for rock in forest.rocks
        if rock.radius > clearance
    ]
    if not discs:
        return False
    centres, radii = np.array(discs)[:, :2], np.array(discs)[:, 2]
    return bool(np.any(np.linalg.norm(centres - position[:2], axis=1) < radii + rover_radius))


def _sense(forest: Forest, pose: np.ndarray, sensor: Sensor) -> np.ndarray:
    """Scan from the LiDAR mounted above the rover; return points in the rover frame."""
    sensor_pose = pose.copy()
    sensor_pose[2, 3] += _NAV["sensor_height_m"]
    scan = simulate_scan(forest, sensor_pose, sensor)
    homogeneous = np.column_stack((scan, np.ones(len(scan))))
    return (np.linalg.inv(pose) @ homogeneous.T).T[:, :3]


def _safe_steer(
    local: np.ndarray, sectors: np.ndarray, goal_heading: float, controller: Controller, step: float
) -> float | None:
    """Steering angle for a safe forward step, or None if no step is safe.

    Try steering towards the goal first, then straight. A candidate is safe if
    the corridor along it is clear and no sensed obstacle point would come
    within rover radius + margin of the rover's next position (this also
    catches obstacles beside the rover that the forward corridor cannot see).
    """
    needed = _NAV["rover_radius_m"] + _NAV["corridor_margin_m"]
    for steer in (controller.forward_steering(sectors, goal_heading), 0.0):
        rotated = _rotate(local, -steer)
        next_xy = np.array([step, 0.0])
        if steer and corridor_clearance(rotated) < controller.safety_distance:
            continue
        if footprint_clearance(rotated, next_xy) >= needed:
            return steer
    return None


def _away(local: np.ndarray) -> float:
    """+1 (turn left) if the closest obstacle point is on the right, else -1."""
    tall = local[(local[:, 2] >= _NAV["obstacle_min_height_m"])
                 & (local[:, 2] <= _NAV["rover_height_m"])]
    if not len(tall):
        return 1.0
    closest = tall[np.argmin(np.linalg.norm(tall[:, :2], axis=1))]
    return 1.0 if closest[1] < 0 else -1.0


def _rotate(points: np.ndarray, angle: float) -> np.ndarray:
    """Rotate rover-frame points about the vertical axis by ``angle`` (rad)."""
    cos, sin = np.cos(angle), np.sin(angle)
    rotated = points.copy()
    rotated[:, 0] = cos * points[:, 0] - sin * points[:, 1]
    rotated[:, 1] = sin * points[:, 0] + cos * points[:, 1]
    return rotated


def _pose_at(position: np.ndarray, heading: float) -> np.ndarray:
    pose = np.eye(4)
    pose[:2, :2] = [[np.cos(heading), -np.sin(heading)], [np.sin(heading), np.cos(heading)]]
    pose[:2, 3] = position[:2]
    return pose


def _heading(pose: np.ndarray) -> float:
    return float(np.arctan2(pose[1, 0], pose[0, 0]))


def _goal_heading(pose: np.ndarray, goal: np.ndarray) -> float:
    """Goal direction relative to the rover's heading, in (-pi, pi], +left."""
    desired = np.arctan2(goal[1] - pose[1, 3], goal[0] - pose[0, 3])
    difference = desired - _heading(pose)
    return float(np.arctan2(np.sin(difference), np.cos(difference)))
