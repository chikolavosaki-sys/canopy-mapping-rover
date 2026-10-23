# Outcomes

## Problem statement

> Wildfire risk depends on ladder fuels, which drones cannot see. We show that a ground LiDAR rover can find them, count trees and measure their thickness, and drive through a forest without hitting things.

## Questions and measurable results

| Question | Metric | Dataset or test source | Target |
|---|---|---|---|
| How well does the pose estimate follow the true path? | Position drift against exact synthetic poses; ATE/RPE against the TreeScope reference trajectory | Simulator, TreeScope | Synthetic drift < 2% of distance travelled |
| Can the system count trees and estimate trunk thickness? | Tree recall and DBH error against field measurements | TreeScope, Shivalik, Weiser | Synthetic DBH RMSE <= 3 cm and recall >= 90%; real-data DBH RMSE <= 5 cm |
| Does the ladder-fuel proxy agree with labelled low vegetation? | Point-density in the 1-4 m and 1-8 m bands compared with shrub labels | DigiForests | Positive correlation and AUC >= 0.75 |
| Can the simulated rover avoid obstacles repeatedly? | Obstacle-avoidance success rate and collision count over repeated runs | Simulator | >= 90% success with 0 collisions over >= 50 runs |

## Final demo

The system processes a forest recording and outputs a map highlighting zones with the most ladder fuel.

Phase 4 adds repeatable simulator navigation metrics: goal success, collision,
timeout, and path length. These metrics describe the synthetic controller only,
not deployment safety on a physical rover.

Phase 2 adds the first forest-analytics path: a grid-lowest-point terrain
model, height normalization, voxel occupancy density, a ladder-fuel proxy
report, and breast-height stem circle fitting. These outputs are intended for
synthetic testing first; the ladder score is not a direct fire-behaviour label.

## Demo results

`python scripts/run_all.py --seed 0 --update-outcomes` regenerates the table
between the markers below (full report: `results/demo/report.md`). It needs no
downloads and takes about 2 minutes. Values are synthetic results, not claims
about real forests.

<!-- demo-results:start -->
Seed 0.

| Metric | Value | Target |
|---|---:|---:|
| Odometry final drift (% of path) | 11.7841 | < 2 % |
| Odometry ATE RMSE (m) | 0.8668 | - |
| Tree recall, scanned map | 0.1667 | >= 0.90 |
| Tree recall, exact-pose map (no odometry error) | 0.8333 | - |
| Tree recall, perfect cloud (upper bound) | 0.8333 | - |
| DBH RMSE (m), scanned map | 0.1889 | <= 0.03 |
| Ladder AUC vs shrub cells, scanned map | 0.8258 | >= 0.75 |
| Navigation runs | 80 | >= 50 |
| Navigation success rate | 0.9375 | >= 0.90 |
| Navigation collisions | 4 | 0 |
<!-- demo-results:end -->

## Honest limits

- The rover is simulated; there is no real rover hardware in this project.
- Ladder fuel is a proxy based on height-band point density, not a direct label.
- Static scans are used for forest analytics, not for odometry.
- The simulated LiDAR ray-casts against simple meshes (cylinder trunks,
  sphere rocks, crowns and shrubs as clusters of small spheres). Real bark,
  foliage, and returns from partly hit objects are messier.
- Odometry suffers from ground degeneracy: smooth-ish ground looks the same
  wherever the rover is, so KISS-ICP under-estimates motion. In the sparse demo
  forest (6 trees in 20 x 20 m) drift is about 12 %; removing ground points
  would cut ATE from 0.74 m to 0.04 m on a 6 m test drive, but KISS-ICP is
  used unmodified. Real data may behave differently.
- Tree recall on the KISS-ICP map is limited by that drift: with exact poses
  the same scans reach the perfect-cloud recall (see the exact-pose column).
- Navigation seeds 0-19 were used for tuning and 1000-1019 for diagnosing the
  blind zone; reported runs use fresh seeds (2000+). Remaining collisions are
  mostly small rocks only a few cm taller than the rover's 0.3 m ground
  clearance, which the per-scan ground plane and sensor noise can hide.
- The rover stays level on slopes (no pitch or roll), and its pose for
  obstacle memory is exact; a real rover would use its own odometry.
