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
  - Tried loosening the DBH thresholds (`min_inlier_fraction` 0.45, `max_fit_residual_m` 0.025, `max_lean_deg` 20) and widening `tree_match_gate_m` to 1.0 m. On demo seed 0 this gave 0.33 recall and 0.33 precision on the KISS-ICP map (2 of 6 detections real).
  - Reverted in review (PR #34): the thresholds were tuned on the same scene the report measures, and a 1.0 m match gate makes matching easier rather than detection better. Fixing the drift itself is tracked in #19.
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

- [Default Configuration](../../configs/default.yaml)
- [End-to-End Demo Script](../../scripts/run_all.py)
- [Demo Results Report](../../results/demo/report.md)
- [System Architecture](../../docs/architecture.md)
