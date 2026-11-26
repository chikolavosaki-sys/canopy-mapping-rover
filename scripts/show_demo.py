"""See the simulator: forest map with a rover drive, one LiDAR scan, and odometry.

    python scripts/show_demo.py            # write PNG figures to results/runs/demo/figures/
    python scripts/show_demo.py --view 3d  # interactive Open3D window (needs a display)
    python scripts/show_demo.py --nav-seed 2000  # inspect a specific navigation scenario

Colours: trunks, shrubs and rocks get the three categorical colours; ground
and crowns are grey context; paths are drawn in dark ink.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

from canopy.evaluation.nav_eval import start_and_goal
from canopy.evaluation.odometry_eval import relative_to_first
from canopy.lidar_odometry import run_kiss_icp, transform_points
from canopy.navigation import Controller
from canopy.simulation.lidar import (
    OdometryMode,
    mapping_frames,
    scan_with_labels,
    simulate_traversal,
)
from canopy.simulation.rover_sim import run_rover
from canopy.simulation.synthetic_forest import (
    Forest,
    make_demo_forest,
    make_forest,
    traversal_poses,
)

INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
COLOURS = {  # reference palette slots 1-3; ground/crown are neutral context
    "stem": "#2a78d6", "shrub": "#eb6834", "rock": "#1baf7a",
    "ground": "#c9c8c3", "crown": "#8f8e89",
}
NAMES = {"stem": "Trunk", "shrub": "Shrub", "rock": "Rock", "ground": "Ground", "crown": "Crown"}


def main() -> None:
    """Build the demo scenes and either save figures or open a 3-D viewer."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--seed", type=int, default=0, help="demo forest seed")
    parser.add_argument("--nav-seed", type=int, default=2006, help="navigation forest seed")
    parser.add_argument("--view", choices=("png", "3d"), default="png")
    parser.add_argument("--viewer-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--out", type=Path, default=Path("results/runs/demo/figures"))
    parser.add_argument(
        "--odometry", choices=("ground-filtered", "all-returns"), default="ground-filtered",
        help="choose which simulated LiDAR returns are used to estimate motion",
    )
    args = parser.parse_args()
    if args.seed < 0 or args.nav_seed < 0:
        parser.error("--seed and --nav-seed must be non-negative")
    if not args.viewer_worker and args.view == "3d" and _launch_viewer(args.seed, args.odometry):
        return
    forest = make_demo_forest(args.seed)
    truth, estimated, scans = _odometry(forest, args.odometry)
    if args.viewer_worker:
        _show_3d(forest, truth, estimated, scans)
        return

    import matplotlib

    # Saving PNGs must work even when the display or its GUI backend failed.
    matplotlib.use("Agg")
    nav_forest = make_forest(args.nav_seed, 30.0, 40)
    start, goal = start_and_goal(nav_forest)
    drive = run_rover(nav_forest, start, goal, Controller())
    args.out.mkdir(parents=True, exist_ok=True)
    _plot_forest_map(nav_forest, drive, args.out / "forest_map.png")
    _plot_scan(forest, traversal_poses(forest)[len(scans) // 2], args.out / "lidar_scan.png")
    _plot_odometry(truth, estimated, args.out / "odometry.png")
    print(f"Wrote forest_map.png, lidar_scan.png, odometry.png to {args.out}/")


def _launch_viewer(seed: int, mode: OdometryMode) -> bool:
    """Isolate Open3D window creation so a native viewer crash can fall back to PNGs."""
    command = [
        sys.executable, str(Path(__file__).resolve()), "--viewer-worker",
        "--seed", str(seed), "--odometry", mode,
    ]
    try:
        result = subprocess.run(command, check=False)
    except OSError as error:
        print(f"Could not start the 3D viewer ({error}). Generating PNG figures.")
        return False
    if result.returncode:
        print(f"3D viewer exited with code {result.returncode}. Generating PNG figures.")
    return result.returncode == 0


def _odometry(forest: Forest, mode: OdometryMode) -> tuple[list, list, list]:
    """Simulate the demo drive and run KISS-ICP; poses are relative to the first."""
    sequence = simulate_traversal(forest, traversal_poses(forest), sensor_frame=True)
    truth = relative_to_first([pose for pose, _ in sequence])
    scans = [scan for _, scan in sequence]
    frames, used_mode = mapping_frames(scans, mode)
    print(f"LiDAR alignment returns: {used_mode}")
    return truth, run_kiss_icp(frames), scans


def _style(axis, title: str) -> None:
    axis.set_title(title, loc="left", color=INK, fontsize=11)
    axis.set_facecolor(SURFACE)
    axis.grid(color=GRID, linewidth=0.6)
    axis.tick_params(colors=MUTED, labelsize=8)
    for spine in axis.spines.values():
        spine.set_visible(False)


def _plot_forest_map(forest: Forest, drive, path: Path) -> None:
    """Top-down map: terrain contours, trunks, shrubs, rocks, and the rover's drive."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    figure, axis = plt.subplots(figsize=(7, 7), facecolor=SURFACE)
    grid = np.linspace(0, forest.plot_size_m, 60)
    x, y = np.meshgrid(grid, grid)
    heights = forest.terrain.height(x, y)
    contours = axis.contour(x, y, heights, levels=10, colors=GRID, linewidths=0.8)
    axis.clabel(contours, fontsize=7, colors=MUTED, fmt="%.1f m")
    for shrub in forest.shrubs:
        (x0, y0, _), (x1, y1, _) = shrub.minimum, shrub.maximum
        box = Rectangle((x0, y0), x1 - x0, y1 - y0, color=COLOURS["shrub"], alpha=0.35, lw=0)
        axis.add_patch(box)
    for tree in forest.trees:
        axis.add_patch(Circle((tree.x, tree.y), tree.dbh / 2, color=COLOURS["stem"]))
    for rock in forest.rocks:
        axis.add_patch(Circle((rock.x, rock.y), rock.radius, color=COLOURS["rock"]))
    route = np.array([pose[:2, 3] for pose in drive.poses])
    axis.plot(route[:, 0], route[:, 1], color=INK, linewidth=2, label="Rover path")
    axis.plot(*route[0], "o", color=INK, markersize=8)
    for text, where in (("start", route[0]), ("end", route[-1])):
        axis.annotate(text, where, xytext=(6, 6), textcoords="offset points", color=INK, fontsize=9)
    outcome = "time-out"
    if drive.reached_goal or drive.collision:
        outcome = "reached goal" if drive.reached_goal else "collision"
    _style(axis, f"Simulated forest, {forest.terrain.slope_deg:.0f}° slope: {outcome}, "
                 f"path ratio {drive.path_ratio:.2f}")
    handles = [Circle((0, 0), color=COLOURS[k], label=n) for k, n in
               (("stem", "Trunk (true size)"), ("shrub", "Shrub"), ("rock", "Rock"))]
    axis.legend(handles=[*handles, axis.lines[0]], loc="upper left", fontsize=8,
                facecolor=SURFACE, edgecolor=GRID, framealpha=1)
    axis.set_aspect("equal")
    axis.set_xlim(0, forest.plot_size_m)
    axis.set_ylim(0, forest.plot_size_m)
    axis.set_xlabel("x (m)", color=MUTED)
    axis.set_ylabel("y (m)", color=MUTED)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _plot_scan(forest: Forest, pose: np.ndarray, path: Path) -> None:
    """One LiDAR scan from above and from the side, coloured by what each ray hit."""
    import matplotlib.pyplot as plt

    points, labels = scan_with_labels(forest, pose)
    figure, (top, side) = plt.subplots(1, 2, figsize=(12, 5.5), facecolor=SURFACE,
                                       gridspec_kw={"width_ratios": [1, 1.4]})
    for name in ("ground", "crown", "shrub", "rock", "stem"):  # context first, objects on top
        chosen = points[labels == name]
        if not len(chosen):
            continue  # e.g. no ray reaches crown height from 0.6 m
        size = 1 if name in ("ground", "crown") else 3
        top.scatter(chosen[:, 0], chosen[:, 1], s=size, color=COLOURS[name], label=NAMES[name],
                    linewidths=0)
        side.scatter(chosen[:, 0], chosen[:, 2], s=size, color=COLOURS[name], linewidths=0)
    sensor_x, sensor_y, sensor_z = pose[:3, 3]
    top.plot(sensor_x, sensor_y, "^", color=INK, markersize=9)
    side.plot(sensor_x, sensor_z, "^", color=INK, markersize=9)
    _style(top, f"One scan from above ({len(points)} points); triangle = LiDAR")
    _style(side, "Same scan from the side (z = height; ground slopes away)")
    top.set_aspect("equal")
    top.set_xlabel("x (m)", color=MUTED)
    top.set_ylabel("y (m)", color=MUTED)
    side.set_xlabel("x (m)", color=MUTED)
    side.set_ylabel("z (m)", color=MUTED)
    top.legend(loc="upper left", fontsize=8, frameon=False, markerscale=4)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _plot_odometry(truth: list, estimated: list, path: Path) -> None:
    """True path vs KISS-ICP estimate, and the position error along the drive."""
    import matplotlib.pyplot as plt

    true_xy = np.array([pose[:2, 3] for pose in truth])
    est_xy = np.array([pose[:2, 3] for pose in estimated])
    est_xyz = np.array([pose[:3, 3] for pose in estimated])
    error = np.linalg.norm(est_xyz - np.array([pose[:3, 3] for pose in truth]), axis=1)
    travelled = np.sum(np.linalg.norm(np.diff(true_xy, axis=0), axis=1))
    figure, (paths, errors) = plt.subplots(1, 2, figsize=(12, 4.5), facecolor=SURFACE)
    paths.plot(true_xy[:, 0], true_xy[:, 1], color=COLOURS["stem"], linewidth=2, label="True path")
    paths.plot(est_xy[:, 0], est_xy[:, 1], color=COLOURS["shrub"], linewidth=2, label="KISS-ICP")
    for xy, colour in ((true_xy, COLOURS["stem"]), (est_xy, COLOURS["shrub"])):
        paths.plot(*xy[-1], "o", color=colour, markersize=8)  # end of each path
    paths.set_aspect("equal")
    paths.legend(loc="lower left", fontsize=8, frameon=False)
    paths.set_xlabel("forward (m)", color=MUTED)
    paths.set_ylabel("sideways (m)", color=MUTED)
    _style(paths, "Path seen from above (relative to the start)")
    errors.plot(np.arange(len(error)), error, color=INK, linewidth=2)
    _style(errors, f"Position error: {error[-1]:.2f} m after {travelled:.1f} m of driving")
    errors.set_xlabel("frame (5 per second)", color=MUTED)
    errors.set_ylabel("error (m)", color=MUTED, labelpad=10)
    errors.set_ylim(bottom=0)
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def _show_3d(forest: Forest, truth: list, estimated: list, scans: list) -> None:
    """Interactive window: exact-pose map coloured by label, true path, KISS-ICP path."""
    import open3d as o3d

    geometries = []
    labelled = [scan_with_labels(forest, pose)
                for pose in traversal_poses(forest)[:: max(1, len(scans) // 10)]]
    for points, labels in labelled:
        cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
        colours = np.array([_rgb(COLOURS[name]) for name in labels])
        cloud.colors = o3d.utility.Vector3dVector(colours)
        geometries.append(cloud)
    start = traversal_poses(forest)[0]
    for poses, colour in ((truth, COLOURS["stem"]), (estimated, COLOURS["shrub"])):
        world = transform_points(np.array([pose[:3, 3] for pose in poses]), start)
        line = o3d.geometry.LineSet(
            o3d.utility.Vector3dVector(world),
            o3d.utility.Vector2iVector([[i, i + 1] for i in range(len(world) - 1)]),
        )
        line.paint_uniform_color(_rgb(colour))
        geometries.append(line)
    viewer = o3d.visualization.Visualizer()
    if not viewer.create_window(window_name="Canopy rover simulator"):
        raise RuntimeError("Open3D could not open a display")
    try:
        for geometry in geometries:
            viewer.add_geometry(geometry)
        print("Blue shows the true path and orange shows KISS-ICP. Press Q to quit.")
        viewer.run()
    finally:
        viewer.destroy_window()


def _rgb(hex_colour: str) -> list[float]:
    return [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]


if __name__ == "__main__":
    main()
