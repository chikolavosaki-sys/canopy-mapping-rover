# Architecture

The project replays recorded LiDAR data and uses a pure-Python/Open3D
simulator for repeatable navigation tests. The core odometry implementation is
KISS-ICP: it is LiDAR-only, pip-installable, and can read ROS1/ROS2 bags
through `rosbags`. FAST-LIO2 is an optional Docker comparison if time permits
(see `docs/fast-lio2-comparison.md`);
it is not a project dependency.

## Phase map

```text
data in:  synthetic forest (simulation) | TreeScope ROS bag | static LAS/PLY plots
            │                               │                     │
            ▼                               ▼                     │
   simulate_scan / traversal        io.bag_reader (rosbags)       │
            └──────────────┬────────────────┘                     │
                           ▼                                      │
              lidar_odometry (KISS-ICP) → TUM poses               │
                           ▼                                      │
                 register → one map cloud ◄───────────────────────┘
                 ┌─────────┴──────────┐
                 ▼                    ▼
   navigation (sectors →      forest_analytics
   state machine, sim only)   ground(CSF) → height-normalise →
                 │            density bands → ladder-fuel index
                 │            stems → DBH table
                 ▼                    ▼
           evaluation: nav success · ATE/RPE (evo) · tree recall/DBH RMSE · ladder vs shrubs
                           ▼
          data out: results/<run>/ — heatmap PNG, CSVs, summary.json, report.md
```

The importable package is `canopy` under `src/canopy/`:

- `canopy.io` loads point clouds and adapts ROS bags.
- `canopy.simulation` creates synthetic forests and rover scans.
- `canopy.lidar_odometry` estimates poses and registers scans.
- `canopy.navigation` contains simulator-only obstacle decisions.
- `canopy.forest_analytics` measures ground-normalised density, ladder-fuel
  proxy, stems, and DBH.
- `canopy.evaluation` compares outputs with synthetic or dataset references.
- `canopy.aerial_context` provides optional overhead indices.

The water-body module remains paused outside this pipeline.

Phase 3 wraps KISS-ICP's `KissICP` class (kiss-icp 1.3.0) frame by frame,
exports TUM trajectories with exact nanosecond timestamps, and merges scans
into one map with `register_scans`. Settings come from the `odometry` section
of `configs/default.yaml`. `canopy-odometry` accepts `--bag` + `--topic`,
`--frames`, or `--synthetic SEED`; the synthetic mode also writes the exact
reference path and ATE/RPE. KISS-ICP is optional at import time; its test is
skipped when the package is missing (as in CI). Scans fed to odometry must be
in the sensor frame (`simulate_traversal(..., sensor_frame=True)`).

Phase 4 adds simulator-only navigation: scans are reduced to forward angular
sectors, a hysteretic controller chooses a movement state, and a unicycle
rover is checked against synthetic stem geometry for collisions. Repeated
seed runs write navigation metrics without claiming real-rover safety.

Phase 5 connects everything in `scripts/run_all.py`: a simulated drive is
tracked with KISS-ICP, the scans are registered into one map, the map is
placed in world coordinates with the known start pose, and forest analytics
run on it. The same analytics also run on the perfect simulated cloud as an
upper bound, so the report shows what scanning and odometry cost. Outputs go
to `results/<run>/` (report, summary JSON, tree list, navigation CSV,
ladder-fuel heatmap); `--update-outcomes` refreshes the table in
`docs/OUTCOMES.md`.

Phase 6 adds instruction-only dataset layout validators, common TUM/tree-table
adapters, and KISS-ICP bag CLI wiring through `rosbags`. Dataset scripts never
download files; users provide local data under ignored paths.

## Open risks

- **TreeScope reference trajectory:** TreeScope processed bags publish
  `/Odometry`, but that trajectory is Faster-LIO output rather than independent
  ground truth. We will call it a *reference trajectory*, not true ground
  truth, when reporting ATE/RPE.
- **Evaluation plan:** Odometry is evaluated using ATE/RPE against the
  TreeScope reference, start-to-end/loop drift on sequences that return near
  their start, and exact poses on the synthetic simulator.
- **IMU availability:** KISS-ICP provides the primary LiDAR-only baseline;
  TreeScope IMU can support future comparison but is not required for Phase 0.
- **No live-driving data:** Recorded datasets cannot prove safe rover driving;
  navigation claims are simulator-only.
- **No ladder-fuel labels:** Ladder fuel remains a height-band occupancy proxy,
  checked against DigiForests shrub labels rather than presented as direct
  biological ground truth.
- **Real-data schema limits:** Shivalik and Weiser field-table column names
  still require confirmation from their released documentation before adding a
  dataset-specific mapping.
