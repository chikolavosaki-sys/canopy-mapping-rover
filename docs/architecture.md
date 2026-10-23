# Architecture

The project replays recorded LiDAR data and uses a pure-Python/Open3D
simulator for repeatable navigation tests. The core odometry implementation is
KISS-ICP: it is LiDAR-only, pip-installable, and can read ROS1/ROS2 bags
through `rosbags`. FAST-LIO2 is an optional Docker comparison if time permits;
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

Phase 3 provides a thin KISS-ICP `OdometryPipeline` wrapper, TUM trajectory
export, and a registered-map helper. KISS-ICP is optional at import time, so
unit tests that do not need it remain runnable without odometry downloads. The
command-line bag wiring remains deliberately deferred until the real-data
adapter phase; current tests use synthetic arrays.

Phase 4 adds simulator-only navigation: scans are reduced to forward angular
sectors, a hysteretic controller chooses a movement state, and a unicycle
rover is checked against synthetic stem geometry for collisions. Repeated
seed runs write navigation metrics without claiming real-rover safety.

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
