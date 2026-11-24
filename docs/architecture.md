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
   state machine, sim only)   ground (CSF) → DTM → height-normalise →
                 │            stems (DBSCAN + RANSAC circle) → DBH table →
                 │            remove stem points → density bands → ladder-fuel index
                 ▼                    ▼
           evaluation: nav success · ATE/RPE · tree recall/DBH RMSE · ladder vs shrubs
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

Forest analytics run in this order (`forest_analytics.pipeline`):
`ground` classifies ground with CSF (RANSAC planes per 5 m tile as fallback),
fits a DTM by local plane fits, and height-normalises; `stems` finds DBH in
the 1.2-1.4 m slice (DBSCAN, RANSAC circle, Kasa + geometric refinement,
arc and verticality checks); stem points are removed; `density` and
`ladder_fuel` then measure height-layer occupancy and the vertical gap. The
registered map keeps 2 cm voxels (`map_voxel_size_m`) because coarser maps
leave too few trunk points for a circle fit.

Machine learning (`canopy.ml`): every point gets 8 local-shape features
(height above ground, linearity, planarity, scattering, verticality, main
direction, height spread, neighbourhood size from its 20 nearest neighbours),
and a Random Forest classifies it as ground, stem, shrub, crown or rock. It is
trained on simulated forests (labels come free from the simulator) and tested
on unseen forests and on real TreeScope VAT-0723 ground/trunk labels
(`scripts/train_point_classifier.py`, results in `results/ml/`).

Phase 3 wraps KISS-ICP's `KissICP` class (kiss-icp 1.3.0) frame by frame,
exports TUM trajectories with exact nanosecond timestamps, and merges scans
into one map with `register_scans`. Settings come from the `odometry` section
of `configs/default.yaml`. `canopy-odometry` accepts `--bag` + `--topic`,
`--frames`, or `--synthetic SEED`; the synthetic mode also writes the exact
reference path and ATE/RPE. KISS-ICP is optional at import time; its test is
skipped when the package is missing (as in CI). Scans fed to odometry must be
in the sensor frame (`simulate_traversal(..., sensor_frame=True)`).

The simulator (`canopy.simulation`) builds a forest on tilted, bumpy ground
(slopes up to 15 deg) with exact ground truth. `simulation.lidar` turns it
into triangle meshes and ray-casts a VLP-16-like scan with Open3D's
`RaycastingScene` (true occlusion, range noise, a label per point).

Phase 4 adds simulator-only navigation. Each step the rover scans from a
LiDAR 0.6 m above its base. Navigation uses 26 beams over 50 degrees to observe
nearby low obstacles on slopes. The mapping sensor uses 16 beams over 30 degrees.
Both profiles retain about two degrees of vertical spacing. See the
[sensor design decision](decisions.md) for the motivation. Each navigation
scan estimates a ground plane (`navigation.terrain`, RANSAC) and remembers obstacle points from the last
8 scans (`navigation.memory`) to cover the LiDAR's close-range blind zone; `navigation.sectors` turns the rover-frame points
into 9 forward sector distances, a rover-wide corridor clearance, and a
footprint clearance. `navigation.controller` is a FORWARD / TURN_LEFT /
TURN_RIGHT / STOP state machine: it turns in place as soon as the corridor is
blocked, commits to one turn side, and resumes only when clear by an extra
margin (hysteresis). FORWARD steers towards the goal only when that direction
and the next footprint are clear. For a nearby goal, the rover checks the
corridor up to the target and can turn in place before completing the approach.
The detection threshold includes a margin for terrain estimation and range
noise. Collisions use trunk cylinders and rock
cross-sections at the rover's ground clearance. `evaluation.nav_eval` runs
seeds x forest densities and writes per-run and per-density CSVs. These are
simulator results, not real-rover safety claims.

Phase 5 connects everything in `scripts/run_all.py`: a simulated drive is
tracked with KISS-ICP. The demo estimates ground height from each scan and
keeps returns above the configured margin for alignment. It uses all returns
if any scan has too few remaining points. Map registration uses the complete
scans and places them in world coordinates with the known start pose. The
standalone `canopy-odometry --synthetic` command shares the demo forest,
alignment modes, and drift metric. Bag and NPY modes align with all valid
returns. The ground filter has been evaluated in simulation. Low logs and
other near-ground features may help align recorded scans.

The analytics also run on the exact-pose map and the perfect simulated cloud to
measure the effects of scan coverage and pose error. The run writes a
registered point cloud, a survey map with paths and detections, a ladder-fuel
heatmap, a tree table, navigation CSVs and a run summary to `results/<run>/`.

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
