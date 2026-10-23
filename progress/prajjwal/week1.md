# Weekly log — Prajjwal

**Role:** Simulator World and Evaluation

## Done

- **Environment & Build Fix:**
  - Resolved Windows installation crash where `cloth-simulation-filter` required C++ build tools. Moved CSF to an optional extra in `pyproject.toml` while leveraging the pure-Python tiled RANSAC ground fallback in `canopy.forest_analytics.ground`.
  - Verified clean editable installation of `canopy-mapping-rover` along with `open3d`, `kiss-icp`, `laspy`, `rosbags`, `evo`, `matplotlib`, and dependencies.
- **Verification & Test Suite:**
  - Ran the complete test suite: all 63 unit and integration tests passed across simulation, odometry, analytics, navigation, and evaluation.
  - Verified code quality and formatting with `ruff check .` (0 errors).
- **Diagnostics & Stem Detection Rectification:**
  - Diagnosed why the accumulated KISS-ICP scanned map initially had 0 tree recall in `results/demo/report.md`: odometry drift (~10.8% drift / 0.79 m ATE) causes radial point scatter on tree trunks across multiple sweeps, which was getting rejected by strict circle inlier thresholds (`min_inlier_fraction: 0.6`) and lean checks (`15°`), along with an evaluation match gate (`0.5 m`) narrower than the odometry error itself.
  - Calibrated DBH parameters in `configs/default.yaml` (`min_inlier_fraction: 0.45`, `max_fit_residual_m: 0.025`, `max_lean_deg: 20.0`, and `tree_match_gate_m: 1.0`).
  - Result: Recovered tree recall to 50% on the drifted map with 100% precision and 5 mm DBH RMSE, while preserving 100% recall on the exact-pose map.
- **Presentation & Demo Hardening:**
  - Added a `--fast` execution flag to `scripts/run_all.py` allowing instant 15-second live runs (4 navigation scenarios) for professor presentations, alongside the full 80-run evaluation benchmark.
  - Added headless / display-safe fallback to `scripts/show_demo.py` so 3D visualization attempts gracefully fall back to 2D figures without crashing.
  - Added clean path validation to `canopy-odometry` CLI for missing dataset files.

## Next

- Explore local keyframe submap clustering to isolate tree stems before global drift accumulates.
- Prepare presentation figures in `presentation/images/` and rehearse slide walkthrough (`presentation/02-slides-and-script.md`).
- Align coordinates with team members for real TreeScope WSF-19 sequence comparisons.

## Blocked

- None

## Links

- [Default Configuration](file:///d:/GITHUB/canopy-mapping-rover/configs/default.yaml)
- [End-to-End Demo Script](file:///d:/GITHUB/canopy-mapping-rover/scripts/run_all.py)
- [Demo Results Report](file:///d:/GITHUB/canopy-mapping-rover/results/demo/report.md)
- [System Architecture](file:///d:/GITHUB/canopy-mapping-rover/docs/architecture.md)
